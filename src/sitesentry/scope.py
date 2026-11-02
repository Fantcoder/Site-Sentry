"""Scope guard and SSRF defence for SiteSentry.

This is the most security-critical module. It decides whether a URL is safe
to request by checking:
  1. Same-origin scope (scheme + registrable domain + port).
  2. Private/reserved IP ranges (SSRF defence), including after DNS resolution.
  3. Decimal/octal/IPv6 IP encoding tricks.

All checks run before each request – not just at parse time.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.parse
from typing import Final

# ---------------------------------------------------------------------------
# Private / reserved ranges to block
# ---------------------------------------------------------------------------

_PRIVATE_V4_NETWORKS: Final[list[ipaddress.IPv4Network]] = [
    ipaddress.IPv4Network("127.0.0.0/8"),  # loopback
    ipaddress.IPv4Network("10.0.0.0/8"),  # RFC 1918
    ipaddress.IPv4Network("172.16.0.0/12"),  # RFC 1918
    ipaddress.IPv4Network("192.168.0.0/16"),  # RFC 1918
    ipaddress.IPv4Network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.IPv4Network("0.0.0.0/8"),  # "this" network
    ipaddress.IPv4Network("100.64.0.0/10"),  # shared address space
    ipaddress.IPv4Network("192.0.0.0/24"),  # IETF protocol assignments
    ipaddress.IPv4Network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.IPv4Network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.IPv4Network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.IPv4Network("240.0.0.0/4"),  # reserved
    ipaddress.IPv4Network("255.255.255.255/32"),  # broadcast
]

_PRIVATE_V6_NETWORKS: Final[list[ipaddress.IPv6Network]] = [
    ipaddress.IPv6Network("::1/128"),  # loopback
    ipaddress.IPv6Network("::/128"),  # unspecified
    ipaddress.IPv6Network("fe80::/10"),  # link-local
    ipaddress.IPv6Network("fc00::/7"),  # unique local
    ipaddress.IPv6Network("::ffff:0:0/96"),  # IPv4-mapped
    ipaddress.IPv6Network("64:ff9b::/96"),  # IPv4/IPv6 translation
    ipaddress.IPv6Network("100::/64"),  # discard
]


class ScopeError(Exception):
    """Raised when a URL is out of scope."""


class PrivateAddressError(Exception):
    """Raised when a URL resolves to a private/reserved address."""


def _normalize_url(url: str) -> str:
    """Return a canonical URL: lowercase scheme+host, strip fragment, normalise port."""
    parsed = urllib.parse.urlparse(url.strip())
    scheme = parsed.scheme.lower()
    host = parsed.hostname or ""
    port = parsed.port

    # Drop default ports
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    netloc = host if port is None else f"{host}:{port}"
    # Reconstruct without fragment
    normalised = urllib.parse.urlunparse(
        (scheme, netloc, parsed.path or "/", parsed.params, parsed.query, "")
    )
    return normalised


def _extract_origin_parts(url: str) -> tuple[str, str, int | None]:
    """Return (scheme, host, port) from a URL. Port is None for scheme defaults."""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    return scheme, host, port


# Regex to detect octal/decimal IP literals (without dots in some forms)
_DECIMAL_IP_RE = re.compile(r"^\d+$")
_OCTAL_SEGMENT_RE = re.compile(r"^0[0-7]+$")


def _resolve_ip_literal(host: str) -> str | None:
    """If host is a decimal or octal IP literal, return the dotted IPv4 string."""
    # Pure decimal (e.g. 2130706433 → 127.0.0.1)
    if _DECIMAL_IP_RE.match(host):
        try:
            n = int(host)
            if 0 <= n <= 0xFFFFFFFF:
                packed = n.to_bytes(4, "big")
                return ".".join(str(b) for b in packed)
        except (ValueError, OverflowError):
            pass

    # Dotted with some octal segments (e.g. 0177.0.0.1 → 127.0.0.1)
    parts = host.split(".")
    if len(parts) == 4:
        resolved = []
        any_octal = False
        for part in parts:
            if _OCTAL_SEGMENT_RE.match(part):
                resolved.append(str(int(part, 8)))
                any_octal = True
            elif part.isdigit():
                resolved.append(part)
            else:
                return None
        if any_octal:
            return ".".join(resolved)

    return None


def is_private_ip(ip_str: str) -> bool:
    """Return True if *ip_str* falls within any private/reserved range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        # Not a valid IP at all – treat as safe (DNS check will catch it)
        return False

    if isinstance(addr, ipaddress.IPv4Address):
        return any(addr in net for net in _PRIVATE_V4_NETWORKS)
    else:  # IPv6
        # Also check IPv4-mapped addresses
        if addr.ipv4_mapped is not None:
            return any(addr.ipv4_mapped in net for net in _PRIVATE_V4_NETWORKS)
        return any(addr in net for net in _PRIVATE_V6_NETWORKS)


def _check_ip_safety(hostname: str, allow_private: bool) -> tuple[bool, str]:
    """Resolve *hostname* via DNS and check every returned IP.

    Returns (safe, reason). Blocking – must be called via asyncio.to_thread.
    """
    if allow_private:
        return True, "private addresses allowed"

    # First: handle IP literals (decimal, octal, IPv6)
    resolved_literal = _resolve_ip_literal(hostname)
    if resolved_literal and is_private_ip(resolved_literal):
        return False, f"IP literal {hostname!r} resolves to private address {resolved_literal}"
        # Looks like a public IP literal; continue

    # Also try parsing as-is (handles IPv6 bracket removal, standard dotted IPv4)
    try:
        addr = ipaddress.ip_address(hostname)
        if is_private_ip(str(addr)):
            return False, f"IP address {hostname!r} is in a private/reserved range"
    except ValueError:
        pass  # not a bare IP literal; do DNS

    # DNS resolution
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return False, f"DNS resolution failed for {hostname!r}: {exc}"

    if not infos:
        return False, f"No DNS records found for {hostname!r}"

    for info in infos:
        ip = info[4][0]
        # Strip IPv6 scope id (e.g. "fe80::1%eth0")
        ip_clean = str(ip).split("%")[0]
        if is_private_ip(ip_clean):
            return (
                False,
                f"Host {hostname!r} resolves to private/reserved address {ip_clean}",
            )

    return True, "ok"


class ScopeGuard:
    """Decides whether a URL is safe and in-scope to request.

    Parameters
    ----------
    target_url:
        The root URL of the scan (e.g. ``https://example.com``).
    allow_private:
        Disable the private-IP guard. Only for local testing.
    """

    def __init__(self, target_url: str, *, allow_private: bool = False) -> None:
        self._target_url = target_url
        self._allow_private = allow_private
        self._scheme, self._host, self._port = _extract_origin_parts(target_url)

        if not self._scheme or not self._host:
            raise ValueError(f"Invalid target URL: {target_url!r}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def origin(self) -> str:
        """Canonical origin: ``scheme://host[:port]``."""
        if self._port is None:
            return f"{self._scheme}://{self._host}"
        return f"{self._scheme}://{self._host}:{self._port}"

    @property
    def host(self) -> str:
        return self._host

    def normalize_url(self, url: str, base: str | None = None) -> str:
        """Resolve *url* relative to *base* (or target), then normalise."""
        if base:
            url = urllib.parse.urljoin(base, url)
        else:
            url = urllib.parse.urljoin(self._target_url, url)
        return _normalize_url(url)

    def is_same_origin(self, url: str) -> bool:
        """True if *url* shares scheme, host, and port with the target."""
        scheme, host, port = _extract_origin_parts(url)
        return scheme == self._scheme and host == self._host and port == self._port

    async def check_ip_safety(self, hostname: str) -> tuple[bool, str]:
        """Async wrapper: resolve hostname and verify no IP is private."""
        import asyncio

        return await asyncio.to_thread(_check_ip_safety, hostname, self._allow_private)

    async def is_url_allowed(self, url: str) -> tuple[bool, str]:
        """Full safety check for *url*: scope + private-IP.

        Returns (allowed, reason).
        """
        parsed = urllib.parse.urlparse(url)

        # Must have http/https scheme
        if parsed.scheme not in ("http", "https"):
            return False, f"Non-HTTP scheme: {parsed.scheme!r}"

        # Must be same origin
        if not self.is_same_origin(url):
            return False, f"Out of scope: {url!r} (target origin: {self.origin})"

        # SSRF guard: check resolved IPs
        hostname = parsed.hostname or ""
        if not hostname:
            return False, "URL has no hostname"

        safe, reason = await self.check_ip_safety(hostname)
        if not safe:
            return False, reason

        return True, "ok"
