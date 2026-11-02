"""Unit tests for the Typer CLI interface."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from sitesentry.cli import app
from sitesentry.models import CheckResult, Finding, ScanResult, ScanStatus, Severity

runner = CliRunner()


class TestCliChecksCommand:
    def test_list_checks(self) -> None:
        result = runner.invoke(app, ["checks"])
        assert result.exit_code == 0
        assert "hdr-csp" in result.stdout
        assert "Content-Security-Policy" in result.stdout


class TestCliScanPermissionGate:
    def test_refuse_without_permission(self) -> None:
        result = runner.invoke(app, ["scan", "https://example.com"])
        assert result.exit_code == 1
        assert "i-have-permission" in result.stderr


class TestCliScanExecution:
    def test_invalid_format(self) -> None:
        result = runner.invoke(
            app, ["scan", "https://example.com", "--i-have-permission", "--format", "invalid"]
        )
        assert result.exit_code == 1
        assert "Invalid format" in result.stderr

    def test_invalid_fail_on(self) -> None:
        result = runner.invoke(
            app, ["scan", "https://example.com", "--i-have-permission", "--fail-on", "unknown"]
        )
        assert result.exit_code == 1
        assert "Invalid --fail-on" in result.stderr

    @patch("sitesentry.aggregator.ScanAggregator.run_scan")
    def test_clean_scan_exit_code_0(self, mock_scan: AsyncMock) -> None:
        import datetime

        mock_scan.return_value = ScanResult(
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
            grade="A",
            score=100,
            results=[],
        )

        result = runner.invoke(
            app, ["scan", "https://example.com", "--i-have-permission", "--fail-on", "high"]
        )
        assert result.exit_code == 0
        assert "Grade:" in result.stderr

    @patch("sitesentry.aggregator.ScanAggregator.run_scan")
    def test_failing_findings_exit_code_2(self, mock_scan: AsyncMock) -> None:
        import datetime

        finding = Finding(
            check_id="hdr-csp",
            title="Missing CSP",
            severity=Severity.high,
            url="https://example.com",
            evidence="none",
            explanation="e",
            fix="f",
        )
        mock_scan.return_value = ScanResult(
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
            grade="C",
            score=85,
            results=[CheckResult(check_id="hdr-csp", findings=[finding])],
        )

        result = runner.invoke(
            app, ["scan", "https://example.com", "--i-have-permission", "--fail-on", "high"]
        )
        assert result.exit_code == 2
        assert "FAIL:" in result.stderr

    @patch("sitesentry.aggregator.ScanAggregator.run_scan")
    def test_output_to_file(self, mock_scan: AsyncMock, tmp_path: Path) -> None:
        import datetime

        mock_scan.return_value = ScanResult(
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
            grade="A",
            score=100,
            results=[],
        )
        out_file = tmp_path / "report.json"
        result = runner.invoke(
            app,
            [
                "scan",
                "https://example.com",
                "--i-have-permission",
                "--output",
                str(out_file),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "https://example.com" in content
