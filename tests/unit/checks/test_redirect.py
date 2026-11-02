"""Unit tests for the HTTPS redirect check."""

from __future__ import annotations

import httpx
import pytest
import respx

from sitesentry.checks.base import ScanContext
from sitesentry.checks.redirect import HttpsRedirectCheck
from sitesentry.config import ScanConfig
from sitesentry.models import Severity


def make_context(target_url: str) -> ScanContext:
    return ScanContext(
        target_url=target_url,
        pages=[],
        soft_404=None,
        config=ScanConfig(target_url=target_url),
        http_client=httpx.AsyncClient(),
    )


class TestHttpsRedirectCheck:
    @pytest.mark.asyncio
    async def test_target_is_http(self) -> None:
        ctx = make_context("http://example.com")
        findings = await HttpsRedirectCheck().run(ctx)
        assert len(findings) == 1
        assert "served over plain HTTP" in findings[0].title
        assert findings[0].severity == Severity.medium

    @pytest.mark.asyncio
    async def test_https_target_with_proper_redirect(self) -> None:
        ctx = make_context("https://example.com")
        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://example.com/").mock(
                return_value=httpx.Response(301, headers={"location": "https://example.com/"})
            )
            findings = await HttpsRedirectCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_https_target_no_redirect(self) -> None:
        ctx = make_context("https://example.com")
        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://example.com/").mock(
                return_value=httpx.Response(200, text="Plain HTTP page")
            )
            findings = await HttpsRedirectCheck().run(ctx)
        assert len(findings) == 1
        assert "does not redirect to HTTPS" in findings[0].title

    @pytest.mark.asyncio
    async def test_https_target_redirects_to_http(self) -> None:
        ctx = make_context("https://example.com")
        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://example.com/").mock(
                return_value=httpx.Response(302, headers={"location": "http://other.com/"})
            )
            findings = await HttpsRedirectCheck().run(ctx)
        assert len(findings) == 1
        assert "does not redirect to HTTPS" in findings[0].title
