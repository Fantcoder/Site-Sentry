"""Unit tests for report generation including SARIF schema validation."""

from __future__ import annotations

import datetime
import json

import pytest

from sitesentry.models import (
    CheckResult,
    Finding,
    ScanResult,
    ScanStatus,
    ScoreBreakdown,
    Severity,
)
from sitesentry.report import ReportGenerator


def make_scan_result() -> ScanResult:
    finding = Finding(
        check_id="hdr-csp",
        title="Content-Security-Policy header missing",
        severity=Severity.medium,
        url="https://example.com",
        evidence="Header not present",
        explanation="No CSP",
        fix="Add CSP header",
    )
    high_finding = Finding(
        check_id="cors-misconfig",
        title="CORS reflects arbitrary origin",
        severity=Severity.high,
        url="https://example.com/api",
        evidence="ACAO: https://sitesentry.invalid",
        explanation="CORS misconfigured",
        fix="Use allowlist",
    )
    return ScanResult(
        scan_id="test-scan-001",
        target_url="https://example.com",
        started_at=datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=datetime.UTC),
        completed_at=datetime.datetime(2024, 1, 15, 10, 1, 0, tzinfo=datetime.UTC),
        status=ScanStatus.completed,
        results=[
            CheckResult(check_id="hdr-csp", title="Content-Security-Policy", findings=[finding]),
            CheckResult(
                check_id="cors-misconfig", title="CORS Misconfiguration", findings=[high_finding]
            ),
        ],
        score=78,
        grade="C",
        page_count=3,
        breakdown=[
            ScoreBreakdown(
                check_id="hdr-csp",
                check_title="CSP",
                finding_count=1,
                raw_deduction=7,
                capped_deduction=7,
            ),
            ScoreBreakdown(
                check_id="cors-misconfig",
                check_title="CORS",
                finding_count=1,
                raw_deduction=15,
                capped_deduction=15,
            ),
        ],
    )


class TestJsonReport:
    def test_valid_json(self) -> None:
        result = make_scan_result()
        json_str = ReportGenerator.to_json(result)
        data = json.loads(json_str)
        assert data["target_url"] == "https://example.com"

    def test_contains_findings(self) -> None:
        result = make_scan_result()
        data = json.loads(ReportGenerator.to_json(result))
        assert len(data["results"]) == 2

    def test_round_trip(self) -> None:
        result = make_scan_result()
        json_str = ReportGenerator.to_json(result)
        data = json.loads(json_str)
        assert data["grade"] == "C"
        assert data["score"] == 78


class TestMarkdownReport:
    def test_contains_header(self) -> None:
        result = make_scan_result()
        md = ReportGenerator.to_markdown(result)
        assert "# SiteSentry Scan Report" in md

    def test_contains_grade(self) -> None:
        result = make_scan_result()
        md = ReportGenerator.to_markdown(result)
        assert "**C**" in md

    def test_contains_findings(self) -> None:
        result = make_scan_result()
        md = ReportGenerator.to_markdown(result)
        assert "hdr-csp" in md

    def test_markdown_with_errors(self) -> None:
        result = make_scan_result()
        result.errors = ["Some error occurred during scan"]
        result.has_incomplete_checks = True
        md = ReportGenerator.to_markdown(result)
        assert "Some error occurred" in md
        assert "Incomplete Checks" in md

        html = ReportGenerator.to_html(result)
        assert "incomplete-warn" in html


class TestHtmlReport:
    def test_is_html(self) -> None:
        result = make_scan_result()
        html = ReportGenerator.to_html(result)
        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html

    def test_self_contained_no_external_links(self) -> None:
        result = make_scan_result()
        html = ReportGenerator.to_html(result)
        # Should not have any CDN links
        assert "cdn.jsdelivr.net" not in html
        assert "googleapis.com" not in html
        assert "cloudflare.com" not in html

    def test_contains_grade_badge(self) -> None:
        result = make_scan_result()
        html = ReportGenerator.to_html(result)
        assert "grade-badge" in html
        assert ">C<" in html

    def test_contains_target_url(self) -> None:
        result = make_scan_result()
        html = ReportGenerator.to_html(result)
        assert "example.com" in html


class TestSarifReport:
    def _load_sarif_schema(self) -> dict:
        """Load the SARIF 2.1.0 schema from the fixtures directory."""
        import os

        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "sarif-schema-2.1.0.json"
        )
        if os.path.exists(schema_path):
            with open(schema_path) as f:
                return json.load(f)
        return {}

    def test_valid_json(self) -> None:
        result = make_scan_result()
        sarif_str = ReportGenerator.to_sarif(result)
        data = json.loads(sarif_str)
        assert data["version"] == "2.1.0"

    def test_has_runs(self) -> None:
        result = make_scan_result()
        data = json.loads(ReportGenerator.to_sarif(result))
        assert "runs" in data
        assert len(data["runs"]) == 1

    def test_tool_driver(self) -> None:
        result = make_scan_result()
        data = json.loads(ReportGenerator.to_sarif(result))
        driver = data["runs"][0]["tool"]["driver"]
        assert driver["name"] == "SiteSentry"

    def test_results_present(self) -> None:
        result = make_scan_result()
        data = json.loads(ReportGenerator.to_sarif(result))
        assert len(data["runs"][0]["results"]) == 2

    def test_severity_mapped_to_level(self) -> None:
        result = make_scan_result()
        data = json.loads(ReportGenerator.to_sarif(result))
        results = data["runs"][0]["results"]
        high_result = next(r for r in results if r["ruleId"] == "cors-misconfig")
        assert high_result["level"] == "error"

    def test_schema_validation(self) -> None:
        """Validate against SARIF 2.1.0 JSON schema if available."""
        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        schema = self._load_sarif_schema()
        if not schema:
            pytest.skip("SARIF schema file not found in tests/fixtures/")

        result = make_scan_result()
        data = json.loads(ReportGenerator.to_sarif(result))
        # Should not raise
        jsonschema.validate(data, schema)
