"""Unit tests for CORS, exposed files, tech disclosure, mixed content, SRI, dir listing."""

from __future__ import annotations

import httpx
import pytest
import respx

from sitesentry.checks.base import ScanContext
from sitesentry.checks.cors import CorsMisconfigCheck
from sitesentry.checks.directory_listing import DirectoryListingCheck
from sitesentry.checks.mixed_content import MixedContentCheck
from sitesentry.checks.sri import SriMissingCheck
from sitesentry.checks.tech_disclosure import TechDisclosureCheck
from sitesentry.config import ScanConfig
from sitesentry.models import PageData, Severity


def make_page(
    url: str = "https://example.com",
    headers: dict[str, str] | None = None,
    body: str = "<html></html>",
    status: int = 200,
    is_https: bool = True,
) -> PageData:
    return PageData(
        url=url,
        status_code=status,
        headers=headers or {},
        body=body,
        is_https=is_https,
    )


def make_context(pages: list[PageData], client: httpx.AsyncClient | None = None) -> ScanContext:
    return ScanContext(
        target_url="https://example.com",
        pages=pages,
        soft_404=None,
        config=ScanConfig(target_url="https://example.com"),
        http_client=client or httpx.AsyncClient(),
    )


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCorsMisconfig:
    @pytest.mark.asyncio
    async def test_reflected_origin_flagged(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com").mock(
                return_value=httpx.Response(
                    200,
                    headers={
                        "access-control-allow-origin": "https://sitesentry.invalid",
                        "access-control-allow-credentials": "true",
                    },
                )
            )
            async with httpx.AsyncClient() as client:
                ctx = make_context([make_page()], client=client)
                findings = await CorsMisconfigCheck().run(ctx)

        assert len(findings) == 1
        assert findings[0].severity == Severity.high

    @pytest.mark.asyncio
    async def test_no_cors_header_clean(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com").mock(return_value=httpx.Response(200))
            async with httpx.AsyncClient() as client:
                ctx = make_context([make_page()], client=client)
                findings = await CorsMisconfigCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_wildcard_with_credentials(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com").mock(
                return_value=httpx.Response(
                    200,
                    headers={
                        "access-control-allow-origin": "*",
                        "access-control-allow-credentials": "true",
                    },
                )
            )
            async with httpx.AsyncClient() as client:
                ctx = make_context([make_page()], client=client)
                findings = await CorsMisconfigCheck().run(ctx)
        assert any(f.severity == Severity.high for f in findings)


# ---------------------------------------------------------------------------
# Tech Disclosure
# ---------------------------------------------------------------------------


class TestTechDisclosure:
    @pytest.mark.asyncio
    async def test_server_header_with_version(self) -> None:
        ctx = make_context([make_page(headers={"server": "Apache/2.4.49"})])
        findings = await TechDisclosureCheck().run(ctx)
        assert any("Server" in f.title for f in findings)
        assert any(f.severity == Severity.low for f in findings)

    @pytest.mark.asyncio
    async def test_x_powered_by(self) -> None:
        ctx = make_context([make_page(headers={"x-powered-by": "PHP/7.4.3"})])
        findings = await TechDisclosureCheck().run(ctx)
        assert any("PHP" in f.evidence for f in findings)

    @pytest.mark.asyncio
    async def test_meta_generator(self) -> None:
        body = '<html><head><meta name="generator" content="WordPress 5.8"></head></html>'
        ctx = make_context([make_page(body=body)])
        findings = await TechDisclosureCheck().run(ctx)
        assert any("generator" in f.title.lower() for f in findings)

    @pytest.mark.asyncio
    async def test_clean_no_version(self) -> None:
        ctx = make_context([make_page(headers={"server": "nginx"})])
        # No version → info level
        findings = await TechDisclosureCheck().run(ctx)
        assert all(f.severity == Severity.info for f in findings)


# ---------------------------------------------------------------------------
# Mixed Content
# ---------------------------------------------------------------------------


class TestMixedContent:
    @pytest.mark.asyncio
    async def test_http_script_on_https_page(self) -> None:
        body = '<html><body><script src="http://cdn.example.com/js.min.js"></script></body></html>'
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await MixedContentCheck().run(ctx)
        assert len(findings) == 1
        assert findings[0].severity == Severity.medium

    @pytest.mark.asyncio
    async def test_https_script_no_finding(self) -> None:
        body = (
            '<html><body><script src="https://cdn.example.com/js.min.js"></script></body></html>'
        )
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await MixedContentCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_http_page_not_checked(self) -> None:
        body = '<html><body><script src="http://cdn.example.com/js.min.js"></script></body></html>'
        ctx = make_context([make_page(url="http://example.com", body=body, is_https=False)])
        findings = await MixedContentCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_relative_url_not_flagged(self) -> None:
        body = '<html><body><script src="/local.js"></script></body></html>'
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await MixedContentCheck().run(ctx)
        assert findings == []


# ---------------------------------------------------------------------------
# SRI Missing
# ---------------------------------------------------------------------------


class TestSriMissing:
    @pytest.mark.asyncio
    async def test_external_script_no_sri(self) -> None:
        body = '<html><head><script src="https://cdn.jsdelivr.net/npm/vue@3.js"></script></head></html>'
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await SriMissingCheck().run(ctx)
        assert len(findings) == 1

    @pytest.mark.asyncio
    async def test_external_script_with_sri(self) -> None:
        body = (
            '<html><head><script src="https://cdn.jsdelivr.net/npm/vue@3.js" '
            'integrity="sha384-abc" crossorigin="anonymous"></script></head></html>'
        )
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await SriMissingCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_same_origin_script_no_finding(self) -> None:
        body = '<html><head><script src="https://example.com/app.js"></script></head></html>'
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await SriMissingCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_external_stylesheet_no_sri(self) -> None:
        body = '<html><head><link rel="stylesheet" href="https://cdn.example.com/style.css"></head></html>'
        ctx = make_context([make_page(body=body, is_https=True)])
        findings = await SriMissingCheck().run(ctx)
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# Directory Listing
# ---------------------------------------------------------------------------


class TestDirectoryListing:
    @pytest.mark.asyncio
    async def test_index_of_detected(self) -> None:
        body = "<html><head><title>Index of /secret/</title></head><body></body></html>"
        ctx = make_context([make_page(body=body)])
        findings = await DirectoryListingCheck().run(ctx)
        assert len(findings) == 1
        assert findings[0].severity == Severity.medium

    @pytest.mark.asyncio
    async def test_normal_page_no_finding(self) -> None:
        body = "<html><head><title>My Site</title></head><body><p>Hello</p></body></html>"
        ctx = make_context([make_page(body=body)])
        findings = await DirectoryListingCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_iis_listing_detected(self) -> None:
        body = "<html><body>[To Parent Directory]<a href='file.txt'>file.txt</a></body></html>"
        ctx = make_context([make_page(body=body)])
        findings = await DirectoryListingCheck().run(ctx)
        assert len(findings) == 1
