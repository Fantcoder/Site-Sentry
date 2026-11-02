"""Unit tests for Pydantic models."""

from __future__ import annotations

import datetime

from sitesentry.models import (
    CheckResult,
    Finding,
    PageData,
    ScanResult,
    Severity,
)


def make_finding(**kwargs: object) -> Finding:
    defaults = dict(
        check_id="hdr-csp",
        title="CSP Missing",
        severity=Severity.medium,
        url="https://example.com",
        evidence="Header not present",
        explanation="No CSP",
        fix="Add CSP",
    )
    defaults.update(kwargs)
    return Finding(**defaults)  # type: ignore[arg-type]


class TestSeverity:
    def test_ordering(self) -> None:
        assert Severity.info < Severity.low
        assert Severity.low < Severity.medium
        assert Severity.medium < Severity.high
        assert Severity.high < Severity.critical
        assert Severity.low.__lt__(123) is NotImplemented
        assert Severity.low.__le__(123) is NotImplemented
        assert Severity.low.__gt__(123) is NotImplemented
        assert Severity.low.__ge__(123) is NotImplemented

    def test_greater_than(self) -> None:
        assert Severity.high > Severity.low

    def test_gte_lte(self) -> None:
        assert Severity.medium >= Severity.medium
        assert Severity.low <= Severity.medium

    def test_weights(self) -> None:
        assert Severity.critical.weight == 25
        assert Severity.high.weight == 15
        assert Severity.medium.weight == 7
        assert Severity.low.weight == 3
        assert Severity.info.weight == 0


class TestFinding:
    def test_dedupe_key_auto_set(self) -> None:
        f = make_finding()
        assert f.dedupe_key != ""
        assert len(f.dedupe_key) == 16

    def test_dedupe_key_consistent(self) -> None:
        f1 = make_finding(check_id="hdr-csp", evidence="Header not present")
        f2 = make_finding(check_id="hdr-csp", evidence="Header not present")
        assert f1.dedupe_key == f2.dedupe_key

    def test_different_evidence_different_key(self) -> None:
        f1 = make_finding(evidence="Header not present")
        f2 = make_finding(evidence="unsafe-inline detected")
        assert f1.dedupe_key != f2.dedupe_key

    def test_explicit_dedupe_key_preserved(self) -> None:
        f = make_finding(dedupe_key="custom_key")
        assert f.dedupe_key == "custom_key"

    def test_serialization_round_trip(self) -> None:
        f = make_finding()
        data = f.model_dump()
        f2 = Finding(**data)
        assert f2.check_id == f.check_id
        assert f2.severity == f.severity


class TestPageData:
    def test_header_case_insensitive(self) -> None:
        page = PageData(
            url="https://example.com",
            status_code=200,
            headers={"Content-Security-Policy": "default-src 'self'"},
        )
        assert page.get_header("content-security-policy") == "default-src 'self'"
        assert page.get_header("CONTENT-SECURITY-POLICY") == "default-src 'self'"

    def test_get_header_default(self) -> None:
        page = PageData(url="https://example.com", status_code=200)
        assert page.get_header("x-custom", "default") == "default"

    def test_is_https_default_false(self) -> None:
        page = PageData(url="http://example.com", status_code=200)
        assert page.is_https is False


class TestScanResult:
    def test_all_findings_flat(self) -> None:
        f1 = make_finding(check_id="hdr-csp")
        f2 = make_finding(check_id="hdr-hsts")
        result = ScanResult(
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            results=[
                CheckResult(check_id="hdr-csp", title="CSP", findings=[f1]),
                CheckResult(check_id="hdr-hsts", title="HSTS", findings=[f2]),
            ],
        )
        assert len(result.all_findings) == 2

    def test_findings_by_severity(self) -> None:
        f_high = make_finding(severity=Severity.high)
        f_low = make_finding(severity=Severity.low)
        result = ScanResult(
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            results=[
                CheckResult(
                    check_id="test",
                    title="Test",
                    findings=[f_high, f_low],
                )
            ],
        )
        by_sev = result.findings_by_severity
        assert len(by_sev[Severity.high]) == 1
        assert len(by_sev[Severity.low]) == 1
