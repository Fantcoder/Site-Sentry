"""Pydantic v2 data models for SiteSentry."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Severity(StrEnum):
    """Finding severity levels, ordered from least to most severe."""

    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

    @property
    def weight(self) -> int:
        """Score-deduction weight for this severity."""
        return _SEVERITY_WEIGHTS[self]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        order = list(Severity)
        return order.index(self) < order.index(other)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        order = list(Severity)
        return order.index(self) > order.index(other)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self == other or self > other


_SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.info: 0,
    Severity.low: 3,
    Severity.medium: 7,
    Severity.high: 15,
    Severity.critical: 25,
}


class ScanStatus(StrEnum):
    """Lifecycle state of a scan."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class OutputFormat(StrEnum):
    """Supported report output formats."""

    json = "json"
    markdown = "md"
    html = "html"
    sarif = "sarif"


# ---------------------------------------------------------------------------
# Core scan data
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    """A single security finding produced by a check."""

    check_id: str = Field(description="Unique check identifier, e.g. 'hdr-csp'")
    title: str = Field(description="Short human-readable title")
    severity: Severity
    url: str = Field(description="The page URL where this was found")
    evidence: str = Field(description="The specific header value, cookie name, etc.")
    explanation: str = Field(description="Why this matters")
    fix: str = Field(description="How to resolve it")
    dedupe_key: str = Field(default="", description="Key for de-duplication across pages")

    @model_validator(mode="after")
    def set_dedupe_key(self) -> Finding:
        if not self.dedupe_key:
            raw = f"{self.check_id}:{self.evidence}"
            self.dedupe_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self


class CheckResult(BaseModel):
    """Output of running a single check."""

    check_id: str
    title: str = ""
    findings: list[Finding] = Field(default_factory=list)
    error: str | None = None
    incomplete: bool = False


class PageData(BaseModel):
    """Data collected for a single crawled page."""

    url: str
    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = Field(default="", description="Decoded body, capped at max_response_size")
    links: list[str] = Field(default_factory=list)
    is_https: bool = False
    content_length: int = 0
    redirect_chain: list[str] = Field(default_factory=list)

    @field_validator("headers", mode="before")
    @classmethod
    def lowercase_header_keys(cls, v: Any) -> dict[str, str]:
        if isinstance(v, dict):
            return {str(k).lower(): str(val) for k, val in v.items()}
        return {}

    def get_header(self, name: str, default: str = "") -> str:
        """Case-insensitive header lookup."""
        return self.headers.get(name.lower(), default)


class ScoreBreakdown(BaseModel):
    """Per-check score deduction detail."""

    check_id: str
    check_title: str
    finding_count: int
    raw_deduction: int
    capped_deduction: int
    findings_summary: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    """Complete result of a scan."""

    scan_id: str = Field(default="")
    target_url: str
    started_at: datetime
    completed_at: datetime | None = None
    status: ScanStatus = ScanStatus.pending
    results: list[CheckResult] = Field(default_factory=list)
    score: int = 0
    grade: str = ""
    breakdown: list[ScoreBreakdown] = Field(default_factory=list)
    page_count: int = 0
    pages_scanned: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    has_incomplete_checks: bool = False

    @property
    def all_findings(self) -> list[Finding]:
        """Flat list of every finding across all check results."""
        findings: list[Finding] = []
        for cr in self.results:
            findings.extend(cr.findings)
        return findings

    @property
    def findings_by_severity(self) -> dict[Severity, list[Finding]]:
        out: dict[Severity, list[Finding]] = {s: [] for s in Severity}
        for f in self.all_findings:
            out[f.severity].append(f)
        return out


class ScanSummary(BaseModel):
    """Lightweight scan record for list views."""

    scan_id: str
    target_url: str
    started_at: datetime
    completed_at: datetime | None = None
    status: ScanStatus
    grade: str
    score: int
    finding_count: int
