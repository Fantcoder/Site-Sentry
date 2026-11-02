"""Unit tests for TLS certificate and protocol checks."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import httpx
import pytest

from sitesentry.checks.base import ScanContext
from sitesentry.checks.tls import TlsCertCheck, TlsProtocolCheck
from sitesentry.config import ScanConfig
from sitesentry.models import Severity


def make_context(target_url: str = "https://example.com") -> ScanContext:
    return ScanContext(
        target_url=target_url,
        pages=[],
        soft_404=None,
        config=ScanConfig(target_url=target_url),
        http_client=httpx.AsyncClient(),
    )


class TestTlsCertCheck:
    @pytest.mark.asyncio
    async def test_skip_non_https(self) -> None:
        ctx = make_context("http://example.com")
        findings = await TlsCertCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_cert_validation_failed(self) -> None:
        ctx = make_context("https://example.com")
        with patch("sitesentry.checks.tls._get_cert_info") as mock_info:
            mock_info.return_value = {
                "cert": None,
                "version": None,
                "error": "certificate verify failed: self-signed certificate",
                "ssl_error": True,
            }
            findings = await TlsCertCheck().run(ctx)

        assert len(findings) == 1
        assert findings[0].severity == Severity.high
        assert "validation failed" in findings[0].title

    @pytest.mark.asyncio
    async def test_cert_expired(self) -> None:
        ctx = make_context("https://example.com")
        past_date = "Jan 01 00:00:00 2020 GMT"
        with patch("sitesentry.checks.tls._get_cert_info") as mock_info:
            mock_info.return_value = {
                "cert": {
                    "notAfter": past_date,
                    "issuer": (("CN", "CA"),),
                    "subject": (("CN", "example.com"),),
                },
                "version": "TLSv1.3",
                "error": None,
                "ssl_error": False,
            }
            findings = await TlsCertCheck().run(ctx)

        assert any("expired" in f.title.lower() for f in findings)
        assert any(f.severity == Severity.high for f in findings)

    @pytest.mark.asyncio
    async def test_cert_expiring_soon(self) -> None:
        ctx = make_context("https://example.com")
        soon = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)
        date_str = soon.strftime("%b %d %H:%M:%S %Y GMT")

        with patch("sitesentry.checks.tls._get_cert_info") as mock_info:
            mock_info.return_value = {
                "cert": {
                    "notAfter": date_str,
                    "issuer": (("CN", "CA"),),
                    "subject": (("CN", "example.com"),),
                },
                "version": "TLSv1.3",
                "error": None,
                "ssl_error": False,
            }
            findings = await TlsCertCheck().run(ctx)

        assert any("14 days" in f.title for f in findings)
        assert any(f.severity == Severity.medium for f in findings)

    @pytest.mark.asyncio
    async def test_cert_self_signed(self) -> None:
        ctx = make_context("https://example.com")
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=100)
        date_str = future.strftime("%b %d %H:%M:%S %Y GMT")
        ident = ((("commonName", "SelfSigned"),),)

        with patch("sitesentry.checks.tls._get_cert_info") as mock_info:
            mock_info.return_value = {
                "cert": {"notAfter": date_str, "issuer": ident, "subject": ident},
                "version": "TLSv1.3",
                "error": None,
                "ssl_error": False,
            }
            findings = await TlsCertCheck().run(ctx)

        assert any("self-signed" in f.title.lower() for f in findings)
        assert any(f.severity == Severity.high for f in findings)


class TestTlsProtocolCheck:
    @pytest.mark.asyncio
    async def test_skip_non_https(self) -> None:
        ctx = make_context("http://example.com")
        findings = await TlsProtocolCheck().run(ctx)
        assert findings == []

    @pytest.mark.asyncio
    async def test_detect_old_tls(self) -> None:
        ctx = make_context("https://example.com")
        with patch("sitesentry.checks.tls._check_old_tls") as mock_check:
            # Accepts TLSv1, rejects TLSv1.1
            mock_check.side_effect = lambda h, p, v: v == "TLSv1"
            findings = await TlsProtocolCheck().run(ctx)

        assert len(findings) == 1
        assert "TLSv1" in findings[0].title
        assert findings[0].severity == Severity.medium
