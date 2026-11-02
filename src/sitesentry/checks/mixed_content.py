"""Mixed content check: HTTP resources on HTTPS pages."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

# Tags and attributes to scan for mixed content
_MIXED_ATTRS: list[tuple[str, str]] = [
    ("script", "src"),
    ("link", "href"),
    ("img", "src"),
    ("iframe", "src"),
    ("object", "data"),
    ("embed", "src"),
    ("audio", "src"),
    ("video", "src"),
    ("source", "src"),
    ("source", "srcset"),
]


class MixedContentCheck(BaseCheck):
    id = "mixed-content"
    title = "Mixed Content"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for page in context.pages:
            # Only applies to HTTPS pages
            if not page.is_https or page.status_code >= 400 or not page.body:
                continue

            soup = BeautifulSoup(page.body, "html.parser")

            for tag, attr in _MIXED_ATTRS:
                for el in soup.find_all(tag, **{attr: True}):
                    val = str(el.get(attr, ""))
                    # srcset may contain multiple URLs
                    urls_to_check = (
                        [v.strip().split()[0] for v in val.split(",")]
                        if attr == "srcset"
                        else [val]
                    )

                    for resource_url in urls_to_check:
                        if resource_url.startswith("http://"):
                            parsed = urlparse(resource_url)
                            is_external = (
                                parsed.netloc and parsed.netloc != urlparse(page.url).netloc
                            )

                            findings.append(
                                Finding(
                                    check_id=self.id,
                                    title="Mixed content: HTTP resource on HTTPS page",
                                    severity=Severity.medium,
                                    url=page.url,
                                    evidence=f"<{tag} {attr}={resource_url!r}>",
                                    explanation=(
                                        f"An HTTPS page loads a resource ({resource_url}) "
                                        "over plain HTTP. This resource can be intercepted "
                                        "and replaced by a network attacker "
                                        "(man-in-the-middle), compromising page integrity."
                                        + (
                                            " The resource is from an external host."
                                            if is_external
                                            else ""
                                        )
                                    ),
                                    fix=(
                                        f"Change the {attr} URL to use https://. "
                                        "If the resource is served by your own server, "
                                        "enable HTTPS there too. "
                                        "Use a Content-Security-Policy with "
                                        "upgrade-insecure-requests as a fallback."
                                    ),
                                )
                            )

        return findings
