"""Targeted unit tests to ensure >=90% test coverage across all modules."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from typer.testing import CliRunner

from sitesentry.aggregator import ScanAggregator
from sitesentry.checks.base import ScanContext
from sitesentry.checks.tls import TlsCertCheck, _check_old_tls, _get_cert_info
from sitesentry.cli import app
from sitesentry.config import ScanConfig
from sitesentry.crawler import Crawler
from sitesentry.scope import ScopeGuard, _check_ip_safety, _resolve_ip_literal

runner = CliRunner()


class TestCliServe:
    @patch("uvicorn.run")
    def test_cli_serve(self, mock_uvicorn: MagicMock) -> None:
        res = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "8001"])
        assert res.exit_code == 0
        assert mock_uvicorn.called


class TestAggregatorExceptions:
    @pytest.mark.asyncio
    async def test_aggregator_scan_timeout(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000", confirm_permission=True, scan_timeout=0.001
        )
        agg = ScanAggregator(cfg)
        with patch.object(agg, "_do_scan", side_effect=TimeoutError()):
            result = await agg.run_scan()
            assert result.status.value == "failed"
            assert any("timed out" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_aggregator_generic_exception(self) -> None:
        cfg = ScanConfig(target_url="http://127.0.0.1:8000", confirm_permission=True)
        agg = ScanAggregator(cfg)
        with patch.object(agg, "_do_scan", side_effect=ValueError("Unexpected crash")):
            result = await agg.run_scan()
            assert result.status.value == "failed"
            assert any("Unexpected crash" in err for err in result.errors)


class TestScopeEdgeCases:
    def test_resolve_ip_literal(self) -> None:
        assert _resolve_ip_literal("2130706433") == "127.0.0.1"
        assert _resolve_ip_literal("0177.0.0.1") == "127.0.0.1"
        assert _resolve_ip_literal("999999999999999999") is None
        assert _resolve_ip_literal("invalid.host.here") is None
        assert _resolve_ip_literal("10.0.0.1") is None  # standard dotted decimal without octal

    def test_check_ip_safety_failures(self) -> None:
        safe, reason = _check_ip_safety(
            "this-domain-definitely-does-not-exist-12345.invalid", allow_private=False
        )
        assert safe is False
        assert "DNS" in reason

    @pytest.mark.asyncio
    async def test_scope_guard_no_hostname(self) -> None:
        g = ScopeGuard("http://localhost:8000", allow_private=True)
        # Empty hostname
        allowed, reason = await g.is_url_allowed("http://:8000")
        assert allowed is False


class TestCrawlerExceptions:
    @pytest.mark.asyncio
    async def test_crawler_robots_and_soft404_errors(self) -> None:
        cfg = ScanConfig(
            target_url="http://127.0.0.1:8000",
            confirm_permission=True,
            allow_private=True,
            max_pages=1,
            rate_limit=50.0,
        )
        scope = ScopeGuard(cfg.target_url, allow_private=True)

        with respx.mock(assert_all_called=False) as mock:
            # Simulate network errors when fetching robots.txt and soft-404
            mock.get("http://127.0.0.1:8000/robots.txt").mock(
                side_effect=httpx.ConnectError("Network down")
            )
            mock.get(url__regex=r"http://127\.0\.0\.1:8000/[a-f0-9]{32}").mock(
                side_effect=httpx.ConnectError("Network down")
            )
            mock.get("http://127.0.0.1:8000/").mock(return_value=httpx.Response(200, text="OK"))

            async with Crawler(cfg, scope) as crawler:
                pages = [p async for p in crawler.crawl()]
                assert len(pages) == 1
                assert crawler.soft_404_page is None


class TestTlsInternalHelpers:
    def test_get_cert_info_oserror(self) -> None:
        with patch("socket.create_connection", side_effect=OSError("Refused")):
            info = _get_cert_info("127.0.0.1", 443)
            assert info["cert"] is None
            assert info["ssl_error"] is False

    def test_check_old_tls_tlsv1_1(self) -> None:
        with patch("socket.create_connection", side_effect=OSError("Connection refused")):
            assert _check_old_tls("127.0.0.1", 443, "TLSv1.1") is False
            assert _check_old_tls("127.0.0.1", 443, "TLSv1.2") is False

    @pytest.mark.asyncio
    async def test_cert_unparseable_date(self) -> None:
        ctx = ScanContext(
            target_url="https://example.com",
            pages=[],
            soft_404=None,
            config=ScanConfig(target_url="https://example.com"),
            http_client=httpx.AsyncClient(),
        )
        with patch("sitesentry.checks.tls._get_cert_info") as mock_info:
            mock_info.return_value = {
                "cert": {"notAfter": "Not A Real Date", "issuer": (), "subject": ()},
                "version": "TLSv1.3",
                "error": None,
                "ssl_error": False,
            }
            findings = await TlsCertCheck().run(ctx)
            assert findings == []
