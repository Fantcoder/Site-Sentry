"""Unit tests for the scan aggregator and crash isolation."""

from __future__ import annotations

import httpx
import pytest
import respx

from sitesentry.aggregator import ScanAggregator, _deduplicate_findings, _run_check_safe
from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.config import ScanConfig
from sitesentry.models import Finding, PageData, Severity


class CrashCheck(BaseCheck):
    id = "crash-check"
    title = "Crashing Check"

    async def run(self, context: ScanContext) -> list[Finding]:
        raise RuntimeError("Simulated unhandled explosion in check!")


class MockGoodCheck(BaseCheck):
    id = "good-check"
    title = "Good Check"

    async def run(self, context: ScanContext) -> list[Finding]:
        return [
            Finding(
                check_id=self.id,
                title="Found an issue",
                severity=Severity.low,
                url=context.target_url,
                evidence="some evidence",
                explanation="expl",
                fix="fix",
            )
        ]


class TestAggregatorCrashIsolation:
    @pytest.mark.asyncio
    async def test_check_exception_is_isolated(self) -> None:
        ctx = ScanContext(
            target_url="http://127.0.0.1:8000",
            pages=[PageData(url="http://127.0.0.1:8000", status_code=200)],
            soft_404=None,
            config=ScanConfig(target_url="http://127.0.0.1:8000", allow_private=True),
            http_client=httpx.AsyncClient(),
        )

        res = await _run_check_safe(CrashCheck, ctx)
        assert res.incomplete is True
        assert res.error is not None
        assert "Simulated unhandled explosion" in res.error
        assert res.findings == []

    @pytest.mark.asyncio
    async def test_full_scan_with_crash_isolation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000",
            confirm_permission=True,
            allow_private=True,
            max_pages=1,
            scan_timeout=10.0,
        )

        # Inject CrashCheck and MockGoodCheck into ALL_CHECKS
        import sitesentry.aggregator as agg_mod

        monkeypatch.setattr(agg_mod, "ALL_CHECKS", [CrashCheck, MockGoodCheck])

        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://127.0.0.1:8000/robots.txt").mock(return_value=httpx.Response(404))
            mock.get(url__regex=r"http://127\.0\.0\.1:8000/[a-f0-9]{32}").mock(
                return_value=httpx.Response(404)
            )
            mock.get("http://127.0.0.1:8000/").mock(
                return_value=httpx.Response(200, text="<html>Hello</html>")
            )

            agg = ScanAggregator(cfg)
            result = await agg.run_scan()

            assert result.status.value == "completed"
            assert result.has_incomplete_checks is True
            # Since incomplete checks exist, grade must not be A
            assert result.grade != "A"
            assert len(result.all_findings) == 1
            assert result.all_findings[0].check_id == "good-check"


class TestDeduplication:
    def test_deduplicate_findings(self) -> None:
        f1 = Finding(
            check_id="hdr-csp",
            title="Missing CSP",
            severity=Severity.medium,
            url="http://example.com/p1",
            evidence="absent",
            explanation="e",
            fix="f",
        )
        f2 = Finding(
            check_id="hdr-csp",
            title="Missing CSP",
            severity=Severity.medium,
            url="http://example.com/p2",
            evidence="absent",
            explanation="e",
            fix="f",
        )
        # Same check_id and evidence produce identical dedupe_key
        assert f1.dedupe_key == f2.dedupe_key
        deduped = _deduplicate_findings([f1, f2])
        assert len(deduped) == 1
        assert deduped[0].url == "http://example.com/p1"
