"""Technology / version disclosure check."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

# Patterns that reveal product + version (e.g. "Apache/2.4.49", "PHP/7.4.3")
_VERSION_PATTERN = re.compile(
    r"(?P<product>[A-Za-z][\w\-.]+)/(?P<version>\d+(?:\.\d+){1,3})",
    re.IGNORECASE,
)

# Headers that commonly reveal tech
_DISCLOSURE_HEADERS = [
    "server",
    "x-powered-by",
    "x-aspnet-version",
    "x-aspnetmvc-version",
    "x-generator",
]


class TechDisclosureCheck(BaseCheck):
    id = "tech-disclosure"
    title = "Technology / Version Disclosure"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for page in context.pages:
            if page.status_code >= 400:
                continue

            # Check response headers
            for header_name in _DISCLOSURE_HEADERS:
                value = page.get_header(header_name)
                if not value:
                    continue

                m = _VERSION_PATTERN.search(value)
                if m:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"{header_name.title()} header reveals version",
                            severity=Severity.low,
                            url=page.url,
                            evidence=f"{header_name}: {value}",
                            explanation=(
                                f"The {header_name!r} header reveals the software product "
                                f"and version ({m.group('product')}/{m.group('version')}). "
                                "This helps attackers identify unpatched software and "
                                "target known CVEs."
                            ),
                            fix=(
                                f"Remove or redact the {header_name!r} header. "
                                "In Apache: ServerTokens Prod. "
                                "In nginx: server_tokens off. "
                                "In PHP: expose_php = Off."
                            ),
                        )
                    )
                elif value.strip():
                    # Product name without version is lower severity
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"{header_name.title()} header discloses technology",
                            severity=Severity.info,
                            url=page.url,
                            evidence=f"{header_name}: {value}",
                            explanation=(
                                f"The {header_name!r} header reveals the underlying technology. "
                                "While no version is shown, this still narrows an attacker's "
                                "fingerprinting effort."
                            ),
                            fix=f"Remove the {header_name!r} header from server responses.",
                        )
                    )

            # Check <meta name="generator" content="...">
            if page.body:
                soup = BeautifulSoup(page.body, "html.parser")
                for meta in soup.find_all("meta", attrs={"name": re.compile(r"generator", re.I)}):
                    content = meta.get("content", "")
                    if content:
                        m = _VERSION_PATTERN.search(content)
                        severity = Severity.low if m else Severity.info
                        findings.append(
                            Finding(
                                check_id=self.id,
                                title="Generator meta tag discloses CMS/framework version",
                                severity=severity,
                                url=page.url,
                                evidence=f'<meta name="generator" content="{content}">',
                                explanation=(
                                    "The HTML generator meta tag reveals the CMS, framework, "
                                    "or tool used to build the page"
                                    + (f" and its version ({m.group(0)})" if m else "")
                                    + ". This aids targeted attacks against known CVEs."
                                ),
                                fix=(
                                    "Remove or redact the generator meta tag. "
                                    "Most CMS platforms have a plugin or setting to hide it."
                                ),
                            )
                        )

        return findings
