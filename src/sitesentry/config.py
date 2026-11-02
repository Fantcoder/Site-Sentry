"""Configuration for SiteSentry using pydantic-settings."""

from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from sitesentry.models import OutputFormat, Severity


class ScanConfig(BaseSettings):
    """Per-scan configuration. Env-var prefix: SITESENTRY_."""

    model_config = SettingsConfigDict(
        env_prefix="SITESENTRY_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Target
    target_url: str = Field(default="", description="URL to scan")

    # Permission gate (safety rule #1)
    confirm_permission: bool = Field(
        default=False,
        description="Must be True to run a scan. Confirms you own/are authorised to test the target.",
    )

    # Crawl limits (safety rule #4)
    max_pages: int = Field(default=50, ge=1, le=500, description="Maximum pages to crawl")
    max_depth: int = Field(default=2, ge=1, le=10, description="Maximum crawl depth")
    rate_limit: float = Field(
        default=2.0, gt=0, le=50.0, description="Requests per second (politeness)"
    )
    request_timeout: float = Field(
        default=10.0, gt=0, le=60.0, description="Per-request timeout in seconds"
    )
    scan_timeout: float = Field(
        default=120.0, gt=0, le=3600.0, description="Global scan timeout in seconds"
    )
    max_response_size: int = Field(
        default=1_048_576,  # 1 MB
        gt=0,
        description="Maximum bytes to read per response",
    )

    # Scope / safety options
    allow_private: bool = Field(
        default=False,
        description="Allow scanning private/loopback IPs (disable SSRF guard). Use only for local testing.",
    )
    respect_robots: bool = Field(
        default=True,
        description="Respect robots.txt disallow rules",
    )
    ignore_robots: bool = Field(
        default=False,
        description="Ignore robots.txt (opt-in override of respect_robots)",
    )

    # Output
    output_format: OutputFormat = Field(
        default=OutputFormat.json,
        description="Report output format",
    )
    output_file: str | None = Field(
        default=None,
        description="Write report to this file instead of stdout",
    )
    fail_on: Severity = Field(
        default=Severity.high,
        description="Exit code 2 if any finding at or above this severity",
    )

    @field_validator("rate_limit")
    @classmethod
    def validate_rate_limit(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("rate_limit must be positive")
        return v

    @property
    def should_respect_robots(self) -> bool:
        """True if robots.txt should be respected (respects ignore_robots override)."""
        return self.respect_robots and not self.ignore_robots

    @property
    def min_delay(self) -> float:
        """Minimum seconds between requests to enforce rate limit."""
        return 1.0 / self.rate_limit


class ApiConfig(BaseSettings):
    """FastAPI service configuration. Env-var prefix: SITESENTRY_API_."""

    model_config = SettingsConfigDict(
        env_prefix="SITESENTRY_API_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bind_host: str = Field(
        default="127.0.0.1",
        description="Host to bind the API server to. Set 0.0.0.0 in Docker.",
    )
    port: int = Field(default=8000, ge=1, le=65535)
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("sitesentry_api_key", "sitesentry_api_api_key", "api_key"),
        description="Optional Bearer token for scan endpoints. Compare with hmac.compare_digest.",
    )
    max_concurrent_scans: int = Field(
        default=3, ge=1, le=20, description="Maximum number of simultaneous background scans"
    )
    per_client_rpm: int = Field(
        default=10, ge=1, description="Maximum scan requests per client per minute"
    )
    db_path: str = Field(default="sitesentry.db", description="SQLite database file path")
