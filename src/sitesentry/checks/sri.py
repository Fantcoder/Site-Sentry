"""Subresource Integrity (SRI) missing check."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity


class SriMissingCheck(BaseCheck):
    id = "sri-missing"
    title = "Subresource Integrity Missing"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for page in context.pages:
            if not page.is_https or page.status_code >= 400 or not page.body:
                continue

            page_host = urlparse(page.url).netloc
            soup = BeautifulSoup(page.body, "html.parser")

            # External <script src="..."> without integrity
            for script in soup.find_all("script", src=True):
                src = str(script.get("src", ""))
                if not src.startswith(("http://", "https://")):
                    continue  # relative or protocol-relative – skip
                if urlparse(src).netloc == page_host:
                    continue  # same origin – SRI optional
                if script.get("integrity"):
                    continue  # already has SRI

                findings.append(
                    Finding(
                        check_id=self.id,
                        title="External script loaded without Subresource Integrity",
                        severity=Severity.low,
                        url=page.url,
                        evidence=f'<script src="{src}">',
                        explanation=(
                            f"The external script {src!r} is loaded without an "
                            "integrity attribute. If the CDN or host is compromised, "
                            "a malicious script could be injected into your page."
                        ),
                        fix=(
                            "Generate an SRI hash: "
                            "openssl dgst -sha384 -binary script.js | openssl base64 -A "
                            'and add integrity="sha384-<hash>" crossorigin="anonymous" '
                            "to the <script> tag."
                        ),
                    )
                )

            # External <link rel="stylesheet" href="..."> without integrity
            for link in soup.find_all("link", href=True):
                rel = link.get("rel", [])
                rel_str = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()
                if "stylesheet" not in rel_str:
                    continue

                href = str(link.get("href", ""))
                if not href.startswith(("http://", "https://")):
                    continue
                if urlparse(href).netloc == page_host:
                    continue
                if link.get("integrity"):
                    continue

                findings.append(
                    Finding(
                        check_id=self.id,
                        title="External stylesheet loaded without Subresource Integrity",
                        severity=Severity.low,
                        url=page.url,
                        evidence=f'<link rel="stylesheet" href="{href}">',
                        explanation=(
                            f"The external stylesheet {href!r} is loaded without an "
                            "integrity attribute. If the CDN or host is compromised, "
                            "malicious CSS could be injected."
                        ),
                        fix=(
                            "Generate an SRI hash for the stylesheet and add "
                            'integrity="sha384-<hash>" crossorigin="anonymous" '
                            "to the <link> tag."
                        ),
                    )
                )

        return findings
