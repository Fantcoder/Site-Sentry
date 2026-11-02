"""Directory listing detection check."""

from __future__ import annotations

import re

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

# Patterns that indicate Apache/nginx/IIS directory listings
_LISTING_PATTERNS = [
    re.compile(r"<title>\s*Index of\s*/", re.IGNORECASE),
    re.compile(r"<h1>\s*Index of\s*/", re.IGNORECASE),
    re.compile(r"<title>\s*Directory listing for\s*/", re.IGNORECASE),
    re.compile(r"\[To Parent Directory\]", re.IGNORECASE),  # IIS
    re.compile(r"<title>\s*\S+\s*- /", re.IGNORECASE),  # nginx style
]


class DirectoryListingCheck(BaseCheck):
    id = "dir-listing"
    title = "Directory Listing Enabled"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for page in context.pages:
            if page.status_code >= 400 or not page.body:
                continue

            for pattern in _LISTING_PATTERNS:
                if pattern.search(page.body):
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title="Directory listing is enabled",
                            severity=Severity.medium,
                            url=page.url,
                            evidence=f"Page body matches directory listing pattern: "
                            f"{pattern.pattern!r}",
                            explanation=(
                                "The web server is configured to display a list of files "
                                "in a directory when no index file is present. This can "
                                "expose sensitive files, source code, backups, and "
                                "internal structure to attackers."
                            ),
                            fix=(
                                "Disable directory listing in your web server configuration. "
                                "Apache: Options -Indexes. "
                                "nginx: autoindex off. "
                                "IIS: Disable Directory Browsing in site settings."
                            ),
                        )
                    )
                    break  # one finding per page is enough

        return findings
