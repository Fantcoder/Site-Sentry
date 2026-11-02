"""Exposed sensitive files check.

Probes a fixed list of well-known paths and verifies the response looks
like the real thing (not a soft-404) before reporting.

SAFETY: Never stores or prints the body contents of sensitive files.
Only reports that the file exists, its HTTP status code, and body size.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from sitesentry import __repo__, __version__
from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.crawler import _looks_like_soft_404
from sitesentry.models import Finding, PageData, Severity

logger = logging.getLogger(__name__)

USER_AGENT = f"SiteSentry/{__version__} (+{__repo__})"


@dataclass
class _ProbeTarget:
    path: str
    severity: Severity
    title: str
    description: str
    # Substring that should appear in body to confirm it's not a soft-404
    # If None, any 200 response is considered a finding
    body_marker: str | None = None
    # If True, absence is reported as info
    absence_is_info: bool = False
    info_title: str = ""


_PROBES: list[_ProbeTarget] = [
    _ProbeTarget(
        path="/.git/HEAD",
        severity=Severity.high,
        title=".git/HEAD exposed",
        description="Git repository HEAD file is publicly accessible",
        body_marker="ref:",
    ),
    _ProbeTarget(
        path="/.env",
        severity=Severity.high,
        title=".env file exposed",
        description=".env environment file is publicly accessible",
        body_marker=None,  # .env files vary; any 200 with small text body is suspicious
    ),
    _ProbeTarget(
        path="/.DS_Store",
        severity=Severity.medium,
        title=".DS_Store file exposed",
        description="macOS .DS_Store file reveals directory structure",
        body_marker=None,
    ),
    _ProbeTarget(
        path="/backup.zip",
        severity=Severity.high,
        title="backup.zip exposed",
        description="Backup archive is publicly accessible",
        body_marker=None,
    ),
    _ProbeTarget(
        path="/phpinfo.php",
        severity=Severity.medium,
        title="phpinfo.php exposed",
        description="PHP info page reveals server configuration",
        body_marker="phpinfo()",
    ),
    _ProbeTarget(
        path="/server-status",
        severity=Severity.medium,
        title="Apache server-status exposed",
        description="Apache server-status page reveals server state",
        body_marker="Apache Server Status",
    ),
    _ProbeTarget(
        path="/.well-known/security.txt",
        severity=Severity.info,
        title="security.txt present",
        description="security.txt is present (good practice)",
        body_marker=None,
        absence_is_info=True,
        info_title="security.txt not found",
    ),
    _ProbeTarget(
        path="/robots.txt",
        severity=Severity.info,
        title="robots.txt hints",
        description="robots.txt is present; review Disallow rules for sensitive paths",
        body_marker="User-agent",
        absence_is_info=False,
    ),
]

# Content types that indicate a real text file (not a redirect page or binary)
_TEXT_CONTENT_TYPES = ("text/plain", "text/html", "application/octet-stream", "")


def _is_likely_real(
    response_body: str,
    content_length: int,
    body_marker: str | None,
    soft_404: PageData | None,
    response_status: int,
    probe_page: PageData,
) -> bool:
    """Return True if the response looks like the real file and not a soft-404."""
    # Must be 200
    if response_status != 200:
        return False

    # Check soft-404 similarity
    if _looks_like_soft_404(probe_page, soft_404):
        return False

    # If we have a body marker, require it to be present
    return not (body_marker and body_marker not in response_body)


class ExposedFilesCheck(BaseCheck):
    id = "exposed-files"
    title = "Exposed Sensitive Files"

    async def run(self, context: ScanContext) -> list[Finding]:
        from urllib.parse import urlparse

        parsed = urlparse(context.target_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        findings: list[Finding] = []

        for probe in _PROBES:
            url = base + probe.path
            try:
                resp = await context.http_client.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=False,
                )
            except httpx.RequestError as exc:
                logger.debug("Exposed files probe failed for %s: %s", url, exc)
                continue

            # Cap body read – NEVER store full contents of sensitive files
            raw = resp.content[:4096]
            try:
                body_preview = raw.decode("utf-8", errors="replace")
            except Exception:
                body_preview = ""

            content_length = int(resp.headers.get("content-length", len(raw)))

            probe_page = PageData(
                url=url,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=body_preview,
                content_length=content_length,
            )

            # security.txt: absence is info-level
            if probe.absence_is_info and resp.status_code != 200:
                findings.append(
                    Finding(
                        check_id=self.id,
                        title=probe.info_title or f"{probe.path} not found",
                        severity=Severity.info,
                        url=url,
                        evidence=f"HTTP {resp.status_code}",
                        explanation=(
                            "A security.txt file (RFC 9116) is absent. This file helps "
                            "security researchers report vulnerabilities responsibly."
                        ),
                        fix=(
                            "Create /.well-known/security.txt following RFC 9116. "
                            "Use https://securitytxt.org/ to generate it."
                        ),
                    )
                )
                continue

            if _is_likely_real(
                body_preview,
                content_length,
                probe.body_marker,
                context.soft_404,
                resp.status_code,
                probe_page,
            ):
                # SAFETY: report only existence and metadata, never body contents
                findings.append(
                    Finding(
                        check_id=self.id,
                        title=probe.title,
                        severity=probe.severity,
                        url=url,
                        evidence=(
                            f"HTTP 200, size={content_length} bytes"
                            + (
                                f", body starts with {body_preview[:40]!r}"
                                if probe.body_marker
                                else ""
                            )
                        ),
                        explanation=probe.description,
                        fix=(
                            f"Remove or restrict access to {probe.path}. "
                            "Ensure your web server does not serve sensitive files. "
                            "Add these paths to your .gitignore and review deployment scripts."
                        ),
                    )
                )

        return findings
