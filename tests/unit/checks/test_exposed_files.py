"""Unit tests for exposed sensitive files check."""

from __future__ import annotations

import httpx
import pytest
import respx

from sitesentry.checks.base import ScanContext
from sitesentry.checks.exposed_files import ExposedFilesCheck
from sitesentry.config import ScanConfig
from sitesentry.models import PageData, Severity


def make_context(client: httpx.AsyncClient, soft_404: PageData | None = None) -> ScanContext:
    return ScanContext(
        target_url="https://example.com",
        pages=[],
        soft_404=soft_404,
        config=ScanConfig(target_url="https://example.com"),
        http_client=client,
    )


class TestExposedFilesCheck:
    @pytest.mark.asyncio
    async def test_exposed_git_head_found(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com/.git/HEAD").mock(
                return_value=httpx.Response(200, text="ref: refs/heads/main\n")
            )
            # 404 for all others
            mock.get(url__regex=r"https://example\.com/(?!\.git/HEAD).*").mock(
                return_value=httpx.Response(404)
            )

            async with httpx.AsyncClient() as client:
                ctx = make_context(client)
                findings = await ExposedFilesCheck().run(ctx)

        git_findings = [
            f for f in findings if f.check_id == "exposed-files" and ".git/HEAD" in f.title
        ]
        assert len(git_findings) == 1
        assert git_findings[0].severity == Severity.high
        assert "ref:" in git_findings[0].evidence

    @pytest.mark.asyncio
    async def test_no_secret_body_leakage(self) -> None:
        """Verify that secret contents from .env are never stored in finding."""
        secret_content = "AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE\nSUPER_SECRET=12345"
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://example.com/.env").mock(
                return_value=httpx.Response(200, text=secret_content)
            )
            mock.get(url__regex=r"https://example\.com/(?!\.env).*").mock(
                return_value=httpx.Response(404)
            )

            async with httpx.AsyncClient() as client:
                ctx = make_context(client)
                findings = await ExposedFilesCheck().run(ctx)

        env_findings = [f for f in findings if ".env" in f.title]
        assert len(env_findings) == 1
        finding = env_findings[0]
        # Ensure the secret values are not in evidence, explanation, or title
        assert "AKIAIOSFODNN7EXAMPLE" not in finding.evidence
        assert "SUPER_SECRET" not in finding.evidence
        assert "AKIAIOSFODNN7EXAMPLE" not in finding.explanation

    @pytest.mark.asyncio
    async def test_soft_404_prevents_false_positives(self) -> None:
        """When server returns 200 with soft-404 body for all paths, exposed files are not flagged."""
        soft_body = "<html><body>Page not found - Custom 404</body></html>"
        soft_404_ref = PageData(
            url="https://example.com/random-probe",
            status_code=200,
            body=soft_body,
            content_length=len(soft_body),
        )

        with respx.mock(assert_all_called=False) as mock:
            # Everything returns 200 with same soft-404 body
            mock.get(url__regex=r"https://example\.com/.*").mock(
                return_value=httpx.Response(200, text=soft_body)
            )

            async with httpx.AsyncClient() as client:
                ctx = make_context(client, soft_404=soft_404_ref)
                findings = await ExposedFilesCheck().run(ctx)

        # Should not flag .git/HEAD, .env, etc., since they match soft-404 response
        critical_or_high = [
            f for f in findings if f.severity in (Severity.high, Severity.critical)
        ]
        assert len(critical_or_high) == 0

    @pytest.mark.asyncio
    async def test_security_txt_absence_reported_as_info(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get(url__regex=r"https://example\.com/.*").mock(return_value=httpx.Response(404))

            async with httpx.AsyncClient() as client:
                ctx = make_context(client)
                findings = await ExposedFilesCheck().run(ctx)

        info_findings = [f for f in findings if "security.txt" in f.title.lower()]
        assert len(info_findings) == 1
        assert info_findings[0].severity == Severity.info
