"""TLS certificate and protocol checks.

Uses stdlib ssl + socket via asyncio.to_thread (blocking calls).
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import socket
import ssl
from urllib.parse import urlparse

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

logger = logging.getLogger(__name__)

_14_DAYS = datetime.timedelta(days=14)
_30_DAYS = datetime.timedelta(days=30)


def _get_cert_info(hostname: str, port: int) -> dict[str, object]:
    """Retrieve TLS certificate info. Blocking – must run in a thread."""
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=10) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=hostname) as ssl_sock:
                cert = ssl_sock.getpeercert()
                version = ssl_sock.version()
                return {"cert": cert, "version": version, "error": None}
    except ssl.SSLCertVerificationError as exc:
        return {"cert": None, "version": None, "error": str(exc), "ssl_error": True}
    except ssl.SSLError as exc:
        return {"cert": None, "version": None, "error": str(exc), "ssl_error": True}
    except OSError as exc:
        return {"cert": None, "version": None, "error": str(exc), "ssl_error": False}


def _check_old_tls(hostname: str, port: int, tls_version: str) -> bool:
    """Return True if the server accepts the given (old) TLS version. Blocking."""
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Restrict to only the target version
        if tls_version == "TLSv1":
            ctx.minimum_version = ssl.TLSVersion.TLSv1
            ctx.maximum_version = ssl.TLSVersion.TLSv1
        elif tls_version == "TLSv1.1":
            ctx.minimum_version = ssl.TLSVersion.TLSv1_1
            ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        else:
            return False
        with socket.create_connection((hostname, port), timeout=5) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=hostname):
                return True
    except Exception:
        return False


class TlsCertCheck(BaseCheck):
    id = "tls-cert"
    title = "TLS Certificate Health"

    async def run(self, context: ScanContext) -> list[Finding]:
        target = context.target_url
        parsed = urlparse(target)

        if parsed.scheme != "https":
            return []  # Not HTTPS – skip

        hostname = parsed.hostname or ""
        port = parsed.port or 443

        info = await asyncio.to_thread(_get_cert_info, hostname, port)
        findings: list[Finding] = []

        if info.get("ssl_error"):
            findings.append(
                Finding(
                    check_id=self.id,
                    title="TLS certificate validation failed",
                    severity=Severity.high,
                    url=target,
                    evidence=str(info.get("error", "SSL error")),
                    explanation=(
                        "The server's TLS certificate could not be validated. This may indicate "
                        "an expired certificate, a hostname mismatch, or a self-signed "
                        "certificate not trusted by the system."
                    ),
                    fix=(
                        "Obtain a valid certificate from a trusted CA (e.g. Let's Encrypt). "
                        "Ensure the certificate matches the hostname and has not expired."
                    ),
                )
            )
            return findings

        if info.get("error"):
            logger.debug("TLS cert check non-SSL error: %s", info["error"])
            return findings  # Connection error – can't determine cert health

        cert = info.get("cert")
        if not cert or not isinstance(cert, dict):
            return findings

        # Check expiry
        not_after = cert.get("notAfter", "")
        if not_after:
            try:
                expiry = datetime.datetime.strptime(
                    str(not_after), "%b %d %H:%M:%S %Y %Z"
                ).replace(tzinfo=datetime.UTC)
                now = datetime.datetime.now(datetime.UTC)
                remaining = expiry - now
                if remaining.total_seconds() < 0:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title="TLS certificate is expired",
                            severity=Severity.high,
                            url=target,
                            evidence=f"notAfter={not_after}",
                            explanation="The server is presenting an expired TLS certificate. "
                            "Browsers will show a security warning, and secure connections "
                            "may be rejected.",
                            fix="Renew the TLS certificate immediately.",
                        )
                    )
                elif remaining < _14_DAYS:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title="TLS certificate expiring within 14 days",
                            severity=Severity.medium,
                            url=target,
                            evidence=f"notAfter={not_after} ({remaining.days} days remaining)",
                            explanation="The certificate will expire very soon. Renew now to "
                            "avoid service disruption.",
                            fix="Renew the TLS certificate immediately.",
                        )
                    )
                elif remaining < _30_DAYS:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title="TLS certificate expiring within 30 days",
                            severity=Severity.low,
                            url=target,
                            evidence=f"notAfter={not_after} ({remaining.days} days remaining)",
                            explanation="The certificate will expire within 30 days. Plan renewal.",
                            fix="Schedule TLS certificate renewal.",
                        )
                    )
            except ValueError as exc:
                logger.debug("Could not parse cert expiry %s: %s", not_after, exc)

        # Check self-signed (issuer == subject)
        issuer = cert.get("issuer", ())
        subject = cert.get("subject", ())
        if issuer and subject and issuer == subject:
            findings.append(
                Finding(
                    check_id=self.id,
                    title="TLS certificate is self-signed",
                    severity=Severity.high,
                    url=target,
                    evidence=f"issuer={issuer}",
                    explanation=(
                        "A self-signed certificate is not trusted by browsers by default. "
                        "Users will see a security warning."
                    ),
                    fix=(
                        "Replace with a certificate issued by a trusted CA "
                        "(e.g. Let's Encrypt, DigiCert)."
                    ),
                )
            )

        return findings


class TlsProtocolCheck(BaseCheck):
    id = "tls-protocol"
    title = "TLS Protocol Version"

    async def run(self, context: ScanContext) -> list[Finding]:
        target = context.target_url
        parsed = urlparse(target)

        if parsed.scheme != "https":
            return []

        hostname = parsed.hostname or ""
        port = parsed.port or 443

        findings: list[Finding] = []

        for version in ("TLSv1", "TLSv1.1"):
            accepts = await asyncio.to_thread(_check_old_tls, hostname, port, version)
            if accepts:
                findings.append(
                    Finding(
                        check_id=self.id,
                        title=f"Server accepts deprecated {version}",
                        severity=Severity.medium,
                        url=target,
                        evidence=f"Server accepted a {version} connection",
                        explanation=(
                            f"{version} is deprecated and has known cryptographic weaknesses "
                            "(e.g. POODLE, BEAST). It should be disabled on the server."
                        ),
                        fix=(
                            f"Disable {version} in your TLS configuration. "
                            "Only TLS 1.2 and 1.3 should be accepted."
                        ),
                    )
                )

        return findings
