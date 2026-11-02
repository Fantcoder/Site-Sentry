"""HTTPS redirect check."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from sitesentry import __repo__, __version__
from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

logger = logging.getLogger(__name__)

USER_AGENT = f"SiteSentry/{__version__} (+{__repo__})"


class HttpsRedirectCheck(BaseCheck):
    id = "redirect-https"
    title = "HTTP to HTTPS Redirect"

    async def run(self, context: ScanContext) -> list[Finding]:
        target = context.target_url
        parsed = urlparse(target)

        # If already HTTP, flag it directly
        if parsed.scheme == "http":
            return [
                Finding(
                    check_id=self.id,
                    title="Site is served over plain HTTP",
                    severity=Severity.medium,
                    url=target,
                    evidence="Target URL uses scheme: http",
                    explanation=(
                        "The site is not using HTTPS. All traffic including credentials "
                        "and session tokens is transmitted in plaintext and can be "
                        "intercepted by anyone on the network path."
                    ),
                    fix=(
                        "Obtain a TLS certificate and configure the server to serve "
                        "all content over HTTPS. Redirect all HTTP traffic to HTTPS."
                    ),
                )
            ]

        # HTTPS target: check if the HTTP version redirects to HTTPS
        http_url = f"http://{parsed.netloc}{parsed.path or '/'}"
        if parsed.query:
            http_url += f"?{parsed.query}"

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=10.0,
                follow_redirects=False,
            ) as client:
                resp = await client.get(http_url)

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location", "")
                if location.startswith("https://"):
                    return []  # Good: HTTP redirects to HTTPS
                return [
                    Finding(
                        check_id=self.id,
                        title="HTTP does not redirect to HTTPS",
                        severity=Severity.medium,
                        url=http_url,
                        evidence=(f"HTTP {resp.status_code} redirect to non-HTTPS: {location!r}"),
                        explanation=(
                            "The server redirects HTTP traffic, but not to an HTTPS URL. "
                            "Users who visit the HTTP version will not be upgraded to HTTPS."
                        ),
                        fix="Ensure the HTTP→HTTPS redirect points to an https:// URL.",
                    )
                ]
            else:
                return [
                    Finding(
                        check_id=self.id,
                        title="HTTP version does not redirect to HTTPS",
                        severity=Severity.medium,
                        url=http_url,
                        evidence=f"HTTP {resp.status_code} (no redirect)",
                        explanation=(
                            "The HTTP version of this site does not redirect to HTTPS. "
                            "Users who type the URL without https:// will get an unencrypted "
                            "connection."
                        ),
                        fix=(
                            "Configure a permanent 301 redirect from all HTTP URLs to the "
                            "corresponding HTTPS URL."
                        ),
                    )
                ]

        except httpx.RequestError as exc:
            logger.debug("Could not reach HTTP version of %s: %s", target, exc)
            return []
