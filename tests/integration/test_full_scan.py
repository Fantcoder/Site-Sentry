"""Integration test running a full scan against the local vulnerable test server."""

from __future__ import annotations

import pytest

from sitesentry.aggregator import ScanAggregator
from sitesentry.config import ScanConfig
from sitesentry.models import ScanStatus, Severity


@pytest.mark.integration
class TestIntegrationFullScan:
    @pytest.mark.asyncio
    async def test_full_scan_against_vulnerable_server(self, vulnerable_server_url: str) -> None:
        """Run an end-to-end scan against the local test server and assert exact findings."""
        cfg = ScanConfig(
            target_url=vulnerable_server_url,
            confirm_permission=True,
            allow_private=True,
            max_pages=10,
            max_depth=2,
            rate_limit=50.0,
            scan_timeout=30.0,
        )

        agg = ScanAggregator(cfg)
        result = await agg.run_scan()

        assert result.status == ScanStatus.completed
        assert result.page_count >= 1
        assert result.score < 100
        # Exposed .git/HEAD and .env are high severity, so grade must be capped at C or worse
        assert result.grade in ("C", "D", "F")

        check_ids_found = {f.check_id for f in result.all_findings}

        # Expected security headers
        assert "hdr-csp" in check_ids_found
        assert "hdr-xfo" in check_ids_found
        assert "hdr-xcto" in check_ids_found
        assert "hdr-referrer" in check_ids_found
        assert "hdr-permissions" in check_ids_found

        # Cookies
        assert "cookie-flags" in check_ids_found

        # Redirect check (HTTP scheme)
        assert "redirect-https" in check_ids_found

        # Technology disclosure (Server Apache & X-Powered-By PHP)
        assert "tech-disclosure" in check_ids_found

        # Exposed files
        assert "exposed-files" in check_ids_found

        # Directory listing on /secret-dir/
        assert "dir-listing" in check_ids_found

        # Check for presence of high severity findings
        high_findings = [
            f for f in result.all_findings if f.severity in (Severity.high, Severity.critical)
        ]
        assert len(high_findings) > 0

    @pytest.mark.asyncio
    async def test_ssrf_blocked_by_default(self, vulnerable_server_url: str) -> None:
        """Ensure that scanning a local private address without allow_private is refused."""
        cfg = ScanConfig(
            target_url=vulnerable_server_url,
            confirm_permission=True,
            allow_private=False,  # SSRF guard active
            max_pages=2,
        )

        agg = ScanAggregator(cfg)
        result = await agg.run_scan()

        # The crawler will refuse to fetch the target URL because 127.0.0.1 is loopback
        assert result.page_count == 0
