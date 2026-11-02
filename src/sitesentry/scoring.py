"""Scoring engine for SiteSentry.

Algorithm (documented in docs/scoring.md):
  1. Collect unique findings per check (de-duplicated by dedupe_key).
  2. For each check: sum the severity weights, cap at MAX_DEDUCTION_PER_CHECK.
  3. Score = max(0, 100 - total_deductions).
  4. Grade from score threshold, with hard caps:
     - Any high/critical finding → grade cannot exceed C.
     - Any incomplete check → grade cannot be A.
"""

from __future__ import annotations

from sitesentry.models import CheckResult, ScoreBreakdown, Severity

# ---------------------------------------------------------------------------
# Configuration (heuristic weights – documented as such in docs/scoring.md)
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.critical: 25,
    Severity.high: 15,
    Severity.medium: 7,
    Severity.low: 3,
    Severity.info: 0,
}

MAX_DEDUCTION_PER_CHECK: int = 30  # cap so one noisy check can't zero the score

GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
]


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def compute_score(
    results: list[CheckResult],
    *,
    has_incomplete: bool = False,
) -> tuple[int, str, list[ScoreBreakdown]]:
    """Compute a 0-100 score, letter grade, and per-check breakdown.

    Returns
    -------
    score:
        Integer score from 0 to 100.
    grade:
        Letter grade A–F.
    breakdown:
        Per-check deduction details.
    """
    breakdown: list[ScoreBreakdown] = []
    total_deduction = 0
    has_high_or_critical = False

    for result in results:
        # De-duplicate findings within this check by dedupe_key
        seen_keys: set[str] = set()
        unique_findings = []
        for f in result.findings:
            if f.dedupe_key not in seen_keys:
                seen_keys.add(f.dedupe_key)
                unique_findings.append(f)

        raw_deduction = sum(SEVERITY_WEIGHTS[f.severity] for f in unique_findings)
        capped_deduction = min(raw_deduction, MAX_DEDUCTION_PER_CHECK)
        total_deduction += capped_deduction

        if any(f.severity in (Severity.high, Severity.critical) for f in unique_findings):
            has_high_or_critical = True

        breakdown.append(
            ScoreBreakdown(
                check_id=result.check_id,
                check_title=result.title,
                finding_count=len(unique_findings),
                raw_deduction=raw_deduction,
                capped_deduction=capped_deduction,
                findings_summary=[
                    f"{f.severity.value.upper()}: {f.title}" for f in unique_findings
                ],
            )
        )

    score = max(0, 100 - total_deduction)
    grade = _score_to_grade(score)

    # Hard cap: high/critical → cannot exceed C
    if has_high_or_critical and grade in ("A", "B"):
        grade = "C"

    # Incomplete check → cannot be A
    if has_incomplete and grade == "A":
        grade = "B"

    return score, grade, breakdown


def _score_to_grade(score: int) -> str:
    """Map a numeric score to a letter grade."""
    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"
