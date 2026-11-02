"""Unit tests for cookie flags check."""

from __future__ import annotations

import httpx
import pytest

from sitesentry.checks.base import ScanContext
from sitesentry.checks.cookies import CookieFlagsCheck
from sitesentry.config import ScanConfig
from sitesentry.models import PageData, Severity


def make_page(cookies: list[str], is_https: bool = True) -> PageData:
    headers: dict[str, str] = {}
    if cookies:
        headers["set-cookie"] = "\n".join(cookies)
    return PageData(
        url="https://example.com" if is_https else "http://example.com",
        status_code=200,
        headers=headers,
        body="<html></html>",
        is_https=is_https,
    )


def make_context(pages: list[PageData]) -> ScanContext:
    return ScanContext(
        target_url="https://example.com",
        pages=pages,
        soft_404=None,
        config=ScanConfig(target_url="https://example.com"),
        http_client=httpx.AsyncClient(),
    )


class TestCookieFlagsCheck:
    @pytest.mark.asyncio
    async def test_secure_cookie_no_findings(self) -> None:
        ctx = make_context([make_page(["session_id=abc; Secure; HttpOnly; SameSite=Lax"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_missing_secure_flag_https(self) -> None:
        ctx = make_context([make_page(["session_id=abc; HttpOnly; SameSite=Lax"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert any("Secure" in f.title for f in findings)

    @pytest.mark.asyncio
    async def test_secure_flag_not_flagged_for_http(self) -> None:
        """Secure flag isn't required on HTTP (already insecure – different check)."""
        ctx = make_context([make_page(["session_id=abc; HttpOnly; SameSite=Lax"], is_https=False)])
        findings = await CookieFlagsCheck().run(ctx)
        # Should not flag Secure missing on HTTP-only pages
        assert not any("Secure" in f.title for f in findings)

    @pytest.mark.asyncio
    async def test_missing_httponly(self) -> None:
        ctx = make_context([make_page(["session_id=abc; Secure; SameSite=Lax"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert any("HttpOnly" in f.title for f in findings)

    @pytest.mark.asyncio
    async def test_missing_samesite(self) -> None:
        ctx = make_context([make_page(["session_id=abc; Secure; HttpOnly"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert any("SameSite" in f.title for f in findings)

    @pytest.mark.asyncio
    async def test_session_cookie_gets_medium_severity(self) -> None:
        ctx = make_context([make_page(["session_id=abc; Secure"])])
        findings = await CookieFlagsCheck().run(ctx)
        # session_id is a session-looking cookie – should be medium
        assert any(f.severity == Severity.medium for f in findings)

    @pytest.mark.asyncio
    async def test_non_session_cookie_gets_low_severity(self) -> None:
        ctx = make_context([make_page(["theme=dark; Secure"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert all(f.severity == Severity.low for f in findings)

    @pytest.mark.asyncio
    async def test_samesite_none_without_secure(self) -> None:
        ctx = make_context([make_page(["session_id=abc; SameSite=None"])])
        findings = await CookieFlagsCheck().run(ctx)
        assert any("SameSite=None" in f.title for f in findings)
        assert any(f.severity == Severity.medium for f in findings)

    @pytest.mark.asyncio
    async def test_error_page_skipped(self) -> None:
        page = PageData(
            url="https://example.com",
            status_code=500,
            headers={"set-cookie": "session_id=abc"},
            is_https=True,
        )
        ctx = make_context([page])
        findings = await CookieFlagsCheck().run(ctx)
        assert findings == []
