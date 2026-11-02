"""Unit tests for the scoring engine."""

from __future__ import annotations

from sitesentry.models import CheckResult, Finding, Severity
from sitesentry.scoring import (
    MAX_DEDUCTION_PER_CHECK,
    SEVERITY_WEIGHTS,
    compute_score,
)


def make_finding(severity: Severity, check_id: str = "test", n: int = 0) -> Finding:
    return Finding(
        check_id=check_id,
        title=f"Test finding {n}",
        severity=severity,
        url="https://example.com",
        evidence=f"evidence {n} {severity.value}",
        explanation="test",
        fix="test fix",
    )


def make_result(check_id: str, findings: list[Finding]) -> CheckResult:
    return CheckResult(check_id=check_id, title=check_id.upper(), findings=findings)


class TestSeverityWeights:
    def test_all_severities_have_weights(self) -> None:
        for sev in Severity:
            assert sev in SEVERITY_WEIGHTS

    def test_critical_highest(self) -> None:
        assert SEVERITY_WEIGHTS[Severity.critical] > SEVERITY_WEIGHTS[Severity.high]

    def test_info_zero(self) -> None:
        assert SEVERITY_WEIGHTS[Severity.info] == 0


class TestComputeScore:
    def test_perfect_score_no_findings(self) -> None:
        results = [make_result("test", [])]
        score, grade, breakdown = compute_score(results)
        assert score == 100
        assert grade == "A"

    def test_single_low_finding(self) -> None:
        results = [make_result("test", [make_finding(Severity.low)])]
        score, grade, breakdown = compute_score(results)
        assert score == 97  # 100 - 3
        assert grade == "A"

    def test_single_medium_finding(self) -> None:
        results = [make_result("test", [make_finding(Severity.medium)])]
        score, grade, breakdown = compute_score(results)
        assert score == 93  # 100 - 7

    def test_single_high_finding(self) -> None:
        results = [make_result("test", [make_finding(Severity.high)])]
        score, grade, breakdown = compute_score(results)
        # Score would be 85 (100-15), but hard cap applies → C
        assert score == 85
        assert grade == "C"

    def test_single_critical_finding(self) -> None:
        results = [make_result("test", [make_finding(Severity.critical)])]
        score, grade, breakdown = compute_score(results)
        assert score == 75
        assert grade == "C"

    def test_cap_per_check(self) -> None:
        """10 low findings = 30 raw, capped at MAX_DEDUCTION_PER_CHECK."""
        findings = [make_finding(Severity.low, n=i) for i in range(10)]
        results = [make_result("test", findings)]
        score, grade, breakdown = compute_score(results)
        assert breakdown[0].raw_deduction == 30  # 10 * 3
        assert breakdown[0].capped_deduction == min(30, MAX_DEDUCTION_PER_CHECK)

    def test_cap_prevents_zero_from_one_check(self) -> None:
        """100 low findings can't zero the score from a single check."""
        findings = [make_finding(Severity.low, n=i) for i in range(100)]
        results = [make_result("test", findings)]
        score, grade, breakdown = compute_score(results)
        assert score >= 100 - MAX_DEDUCTION_PER_CHECK

    def test_deduplication(self) -> None:
        """Identical findings (same dedupe_key) counted only once."""
        f = make_finding(Severity.medium)
        # Both have the same dedupe_key
        results = [make_result("test", [f, f])]
        score, grade, breakdown = compute_score(results)
        # Should only deduct once (7), not twice
        assert score == 93

    def test_grade_boundary_a(self) -> None:
        results = [make_result("test", [])]
        score, grade, _ = compute_score(results)
        assert grade == "A"

    def test_grade_boundary_b(self) -> None:
        # Need score 89
        findings = [make_finding(Severity.low, n=i) for i in range(4)]  # -12 → 88
        # Add 4 lows (12 points): score = 88 → B
        results = [make_result("test", findings)]
        score, grade, _ = compute_score(results)
        assert 80 <= score < 90
        assert grade == "B"

    def test_grade_boundary_f(self) -> None:
        # Need score < 60: use multiple checks
        results = [
            make_result(
                f"check-{i}",
                [make_finding(Severity.medium, check_id=f"check-{i}", n=j) for j in range(10)],
            )
            for i in range(10)
        ]
        score, grade, _ = compute_score(results)
        assert grade in ("D", "F")

    def test_high_finding_caps_grade_at_c(self) -> None:
        """Even with score >= 90, a high finding caps grade at C."""
        results = [make_result("test", [make_finding(Severity.high)])]
        score, grade, _ = compute_score(results)
        assert grade == "C"

    def test_incomplete_check_prevents_a(self) -> None:
        """If any check is incomplete and score = 100, grade becomes B."""
        results: list[CheckResult] = []  # no findings → score 100
        score, grade, _ = compute_score(results, has_incomplete=True)
        assert score == 100
        assert grade == "B"  # downgraded from A

    def test_breakdown_structure(self) -> None:
        results = [make_result("hdr-csp", [make_finding(Severity.medium)])]
        _, _, breakdown = compute_score(results)
        assert len(breakdown) == 1
        assert breakdown[0].check_id == "hdr-csp"
        assert breakdown[0].finding_count == 1
        assert breakdown[0].raw_deduction == 7

    def test_multiple_checks(self) -> None:
        results = [
            make_result("hdr-csp", [make_finding(Severity.medium)]),  # -7
            make_result("hdr-hsts", [make_finding(Severity.medium)]),  # -7
        ]
        score, grade, _ = compute_score(results)
        assert score == 86  # 100 - 14

    def test_score_to_grade_f(self) -> None:
        from sitesentry.scoring import _score_to_grade

        assert _score_to_grade(50) == "F"
        assert _score_to_grade(-5) == "F"
