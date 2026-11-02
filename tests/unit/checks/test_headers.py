"""Unit tests for security header checks."""

from __future__ import annotations

import httpx
import pytest

from sitesentry.checks.base import ScanContext
from sitesentry.checks.headers import (
    CspCheck,
    HstsCheck,
    PermissionsPolicyCheck,
    ReferrerPolicyCheck,
    XctoCheck,
    XfoCheck,
)
from sitesentry.config import ScanConfig
from sitesentry.models import PageData, Severity


def make_page(
    url: str = "https://example.com",
    headers: dict | None = None,
    status: int = 200,
    is_https: bool = True,
) -> PageData:
    if headers is None:
        headers = {}
    return PageData(
        url=url,
        status_code=status,
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


class TestCspCheck:
    @pytest.mark.asyncio
    async def test_missing_csp(self) -> None:
        ctx = make_context([make_page(headers={})])
        findings = await CspCheck().run(ctx)
        assert len(findings) == 1
        assert findings[0].check_id == "hdr-csp"
        assert findings[0].severity == Severity.medium

    @pytest.mark.asyncio
    async def test_good_csp(self) -> None:
        ctx = make_context([make_page(headers={"content-security-policy": "default-src 'self'"})])
        findings = await CspCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_unsafe_inline_flagged(self) -> None:
        ctx = make_context(
            [make_page(headers={"content-security-policy": "default-src 'self' 'unsafe-inline'"})]
        )
        findings = await CspCheck().run(ctx)
        assert any("unsafe-inline" in f.evidence or "unsafe" in f.title.lower() for f in findings)

    @pytest.mark.asyncio
    async def test_wildcard_flagged(self) -> None:
        ctx = make_context([make_page(headers={"content-security-policy": "default-src *"})])
        findings = await CspCheck().run(ctx)
        assert any("wildcard" in f.title.lower() for f in findings)

    @pytest.mark.asyncio
    async def test_error_page_skipped(self) -> None:
        ctx = make_context([make_page(status=404)])
        findings = await CspCheck().run(ctx)
        assert findings == []


class TestHstsCheck:
    @pytest.mark.asyncio
    async def test_missing_hsts_https(self) -> None:
        ctx = make_context([make_page(is_https=True)])
        findings = await HstsCheck().run(ctx)
        assert any(f.check_id == "hdr-hsts" for f in findings)

    @pytest.mark.asyncio
    async def test_hsts_skipped_for_http(self) -> None:
        ctx = make_context([make_page(url="http://example.com", is_https=False)])
        findings = await HstsCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_good_hsts(self) -> None:
        ctx = make_context(
            [
                make_page(
                    headers={"strict-transport-security": "max-age=31536000; includeSubDomains"}
                )
            ]
        )
        findings = await HstsCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_short_max_age_flagged(self) -> None:
        ctx = make_context([make_page(headers={"strict-transport-security": "max-age=86400"})])
        findings = await HstsCheck().run(ctx)
        assert any("max-age" in f.title.lower() for f in findings)

    @pytest.mark.asyncio
    async def test_missing_includesubdomains(self) -> None:
        ctx = make_context([make_page(headers={"strict-transport-security": "max-age=31536000"})])
        findings = await HstsCheck().run(ctx)
        assert any("includesubdomains" in f.title.lower() for f in findings)


class TestXfoCheck:
    @pytest.mark.asyncio
    async def test_missing_xfo(self) -> None:
        ctx = make_context([make_page()])
        findings = await XfoCheck().run(ctx)
        assert len(findings) == 1

    @pytest.mark.asyncio
    async def test_xfo_present(self) -> None:
        ctx = make_context([make_page(headers={"x-frame-options": "DENY"})])
        findings = await XfoCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_csp_frame_ancestors_accepted(self) -> None:
        ctx = make_context(
            [make_page(headers={"content-security-policy": "frame-ancestors 'self'"})]
        )
        findings = await XfoCheck().run(ctx)
        assert findings == []


class TestXctoCheck:
    @pytest.mark.asyncio
    async def test_missing_xcto(self) -> None:
        ctx = make_context([make_page()])
        findings = await XctoCheck().run(ctx)
        assert len(findings) == 1

    @pytest.mark.asyncio
    async def test_nosniff_present(self) -> None:
        ctx = make_context([make_page(headers={"x-content-type-options": "nosniff"})])
        findings = await XctoCheck().run(ctx)
        assert findings == []


class TestReferrerPolicyCheck:
    @pytest.mark.asyncio
    async def test_missing_referrer_policy(self) -> None:
        ctx = make_context([make_page()])
        findings = await ReferrerPolicyCheck().run(ctx)
        assert len(findings) == 1
        assert findings[0].severity == Severity.info

    @pytest.mark.asyncio
    async def test_referrer_policy_present(self) -> None:
        ctx = make_context(
            [make_page(headers={"referrer-policy": "strict-origin-when-cross-origin"})]
        )
        findings = await ReferrerPolicyCheck().run(ctx)
        assert findings == []


class TestPermissionsPolicyCheck:
    @pytest.mark.asyncio
    async def test_missing_permissions_policy(self) -> None:
        ctx = make_context([make_page()])
        findings = await PermissionsPolicyCheck().run(ctx)
        assert len(findings) == 1
        assert findings[0].severity == Severity.info

    @pytest.mark.asyncio
    async def test_permissions_policy_present(self) -> None:
        ctx = make_context([make_page(headers={"permissions-policy": "camera=(), microphone=()"})])
        findings = await PermissionsPolicyCheck().run(ctx)
        assert findings == []
