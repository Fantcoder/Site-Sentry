"""Async web crawler for SiteSentry.

Crawls same-origin pages with BFS, rate limiting, robots.txt respect,
and soft-404 detection. Handles redirects manually so each hop is
checked against the scope guard before following.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from collections.abc import AsyncIterator
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from sitesentry import __repo__, __version__
from sitesentry.config import ScanConfig
from sitesentry.models import PageData
from sitesentry.scope import ScopeGuard

logger = logging.getLogger(__name__)

USER_AGENT = f"SiteSentry/{__version__} (+{__repo__})"

# Tags and attributes to extract links from
_LINK_ATTRS: list[tuple[str, str]] = [
    ("a", "href"),
    ("link", "href"),
    ("script", "src"),
    ("img", "src"),
    ("iframe", "src"),
    ("form", "action"),
]


class PermissionDeniedError(Exception):
    """Raised when a scan is attempted without the permission flag."""


class CrawlError(Exception):
    """General crawl error."""


def _strip_fragment(url: str) -> str:
    """Remove URL fragment (everything after #)."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, p.query, ""))


def _parse_robots(content: str, base_url: str) -> RobotFileParser:
    """Parse robots.txt content and return a configured parser."""
    parser = RobotFileParser(url=base_url)
    parser.parse(content.splitlines())
    return parser


def _extract_links_from_html(html: str, base_url: str) -> list[str]:
    """Extract all href/src links from HTML, resolved relative to base_url."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag, attr in _LINK_ATTRS:
        for el in soup.find_all(tag, **{attr: True}):
            val = el.get(attr, "")
            if not val or val.startswith(("data:", "javascript:", "mailto:", "#")):
                continue
            resolved = urljoin(base_url, val)
            links.append(_strip_fragment(resolved))
    return links


class Crawler:
    """Async BFS web crawler.

    Usage::

        async with Crawler(config, scope) as crawler:
            async for page in crawler.crawl():
                process(page)
    """

    def __init__(self, config: ScanConfig, scope: ScopeGuard) -> None:
        self._config = config
        self._scope = scope
        self._client: httpx.AsyncClient | None = None
        self._rate_semaphore = asyncio.Semaphore(1)  # serialise requests for rate limiting
        self._last_request_time: float = 0.0
        self._robots: RobotFileParser | None = None
        self._soft_404: PageData | None = None

    async def __aenter__(self) -> Crawler:
        self._client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=httpx.Timeout(self._config.request_timeout),
            follow_redirects=False,  # handle manually for SSRF re-check
            verify=True,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._client:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def soft_404_page(self) -> PageData | None:
        """Reference page used to detect soft-404s. Available after crawl()."""
        return self._soft_404

    async def crawl(self) -> AsyncIterator[PageData]:
        """Yield PageData for each successfully crawled page.

        Raises PermissionDeniedError if confirm_permission is False.
        """
        if not self._config.confirm_permission:
            raise PermissionDeniedError(
                "Scan refused: --i-have-permission flag not set. "
                "Only scan sites you own or are authorised to test."
            )

        if self._client is None:
            raise CrawlError("Crawler must be used as async context manager")

        target = self._config.target_url

        # 1. Fetch robots.txt
        if self._config.should_respect_robots:
            self._robots = await self._fetch_robots(target)

        # 2. Detect soft-404 (fetch a random nonexistent path)
        self._soft_404 = await self._fetch_soft_404(target)

        # 3. BFS crawl
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((self._scope.normalize_url(target), 0))

        pages_crawled = 0

        while queue and pages_crawled < self._config.max_pages:
            url, depth = queue.popleft()

            if url in visited:
                continue
            visited.add(url)

            # Check scope + SSRF before fetching
            allowed, reason = await self._scope.is_url_allowed(url)
            if not allowed:
                logger.debug("Skipping %s: %s", url, reason)
                continue

            # Check robots.txt
            if self._robots and not self._robots.can_fetch(USER_AGENT, url):
                logger.debug("robots.txt disallows %s", url)
                continue

            page = await self._fetch_page(url)
            if page is None:
                continue

            pages_crawled += 1
            yield page

            # Enqueue links if not at max depth
            if depth < self._config.max_depth:
                for link in page.links:
                    norm = self._scope.normalize_url(link)
                    if norm not in visited:
                        queue.append((norm, depth + 1))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _rate_limited_request(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        """Issue a request, enforcing the configured rate limit."""
        if self._client is None:
            raise CrawlError("Crawler client not initialized")

        async with self._rate_semaphore:
            # Enforce minimum delay since last request
            elapsed = time.monotonic() - self._last_request_time
            delay = self._config.min_delay - elapsed
            if delay > 0:
                await asyncio.sleep(delay)

            resp = await self._client.request(method, url, **kwargs)  # type: ignore[arg-type]
            self._last_request_time = time.monotonic()
            return resp

    async def _follow_redirects(
        self,
        url: str,
        max_hops: int = 10,
    ) -> tuple[httpx.Response, list[str]]:
        """Follow redirects manually, re-checking scope + SSRF at each hop.

        Returns (final_response, redirect_chain).
        Raises ScopeError / PrivateAddressError if any hop is blocked.
        """
        chain: list[str] = []
        current = url

        for _ in range(max_hops):
            resp = await self._rate_limited_request("GET", current)

            if resp.status_code not in (301, 302, 303, 307, 308):
                return resp, chain

            location = resp.headers.get("location", "")
            if not location:
                return resp, chain

            next_url = urljoin(current, location)
            next_url = _strip_fragment(next_url)
            chain.append(next_url)

            # Re-check scope and SSRF for redirect target
            allowed, reason = await self._scope.is_url_allowed(next_url)
            if not allowed:
                logger.warning("Redirect blocked: %s → %s (%s)", current, next_url, reason)
                # Return the redirect response itself (don't follow)
                return resp, chain

            current = next_url

        # Too many redirects — return last response
        resp = await self._rate_limited_request("GET", current)
        return resp, chain

    async def _fetch_page(self, url: str) -> PageData | None:
        """Fetch *url* and return a PageData, or None on error."""
        if self._client is None:
            raise CrawlError("Crawler client not initialized")
        try:
            resp, redirect_chain = await self._follow_redirects(url)
        except httpx.RequestError as exc:
            logger.warning("Request error fetching %s: %s", url, exc)
            return None
        except Exception as exc:
            logger.warning("Unexpected error fetching %s: %s", url, exc)
            return None

        # Cap body size
        raw_body = resp.content[: self._config.max_response_size]
        try:
            body = raw_body.decode(resp.encoding or "utf-8", errors="replace")
        except (LookupError, UnicodeDecodeError):
            body = raw_body.decode("utf-8", errors="replace")

        content_type = resp.headers.get("content-type", "")
        is_html = "html" in content_type.lower()

        links: list[str] = []
        if is_html:
            links = _extract_links_from_html(body, url)

        return PageData(
            url=url,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=body,
            links=links,
            is_https=url.startswith("https://"),
            content_length=len(raw_body),
            redirect_chain=redirect_chain,
        )

    async def _fetch_robots(self, base_url: str) -> RobotFileParser | None:
        """Fetch and parse robots.txt. Returns None on error."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            resp = await self._rate_limited_request("GET", robots_url)
            if resp.status_code == 200:
                content = resp.text
                parser = _parse_robots(content, robots_url)
                logger.debug("Fetched robots.txt from %s", robots_url)
                return parser
        except Exception as exc:
            logger.debug("Could not fetch robots.txt: %s", exc)

        return None

    async def _fetch_soft_404(self, base_url: str) -> PageData | None:
        """Fetch a random nonexistent path to detect soft-404 responses."""
        random_path = f"/{uuid.uuid4().hex}"
        parsed = urlparse(base_url)
        soft_404_url = f"{parsed.scheme}://{parsed.netloc}{random_path}"

        try:
            resp = await self._rate_limited_request("GET", soft_404_url)
            raw_body = resp.content[: self._config.max_response_size]
            try:
                body = raw_body.decode(resp.encoding or "utf-8", errors="replace")
            except (LookupError, UnicodeDecodeError):
                body = raw_body.decode("utf-8", errors="replace")

            return PageData(
                url=soft_404_url,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=body,
                links=[],
                is_https=soft_404_url.startswith("https://"),
                content_length=len(raw_body),
            )
        except Exception as exc:
            logger.debug("Could not fetch soft-404 probe: %s", exc)
            return None


def _looks_like_soft_404(page: PageData, soft_404: PageData | None) -> bool:
    """Return True if *page* looks like a soft-404 (not a real finding).

    Compares status code and content-length similarity to the soft-404 probe.
    """
    if soft_404 is None:
        return False
    # Same status code as the soft-404 probe → likely a soft-404
    if page.status_code == soft_404.status_code and soft_404.content_length > 0:
        ratio = abs(page.content_length - soft_404.content_length) / soft_404.content_length
        if ratio < 0.1:
            return True
    return False


# Re-export for use in checks
__all__ = ["CrawlError", "Crawler", "PermissionDeniedError", "_looks_like_soft_404"]
