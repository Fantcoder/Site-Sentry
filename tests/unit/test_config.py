"""Unit tests for configuration classes."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sitesentry.config import ApiConfig, ScanConfig
from sitesentry.models import OutputFormat, Severity


class TestScanConfig:
    def test_default_values(self) -> None:
        cfg = ScanConfig()
        assert cfg.target_url == ""
        assert cfg.confirm_permission is False
        assert cfg.max_pages == 50
        assert cfg.max_depth == 2
        assert cfg.rate_limit == 2.0
        assert cfg.request_timeout == 10.0
        assert cfg.scan_timeout == 120.0
        assert cfg.max_response_size == 1_048_576
        assert cfg.allow_private is False
        assert cfg.respect_robots is True
        assert cfg.ignore_robots is False
        assert cfg.output_format == OutputFormat.json
        assert cfg.output_file is None
        assert cfg.fail_on == Severity.high

    def test_robots_resolution(self) -> None:
        cfg = ScanConfig(respect_robots=True, ignore_robots=False)
        assert cfg.should_respect_robots is True

        cfg_ignored = ScanConfig(respect_robots=True, ignore_robots=True)
        assert cfg_ignored.should_respect_robots is False

        cfg_disabled = ScanConfig(respect_robots=False, ignore_robots=False)
        assert cfg_disabled.should_respect_robots is False

    def test_min_delay(self) -> None:
        cfg = ScanConfig(rate_limit=2.0)
        assert cfg.min_delay == 0.5
        cfg_fast = ScanConfig(rate_limit=10.0)
        assert cfg_fast.min_delay == 0.1

    def test_invalid_rate_limit(self) -> None:
        with pytest.raises(ValidationError):
            ScanConfig(rate_limit=0.0)
        with pytest.raises(ValidationError):
            ScanConfig(rate_limit=-1.0)

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SITESENTRY_MAX_PAGES", "12")
        monkeypatch.setenv("SITESENTRY_ALLOW_PRIVATE", "true")
        cfg = ScanConfig()
        assert cfg.max_pages == 12
        assert cfg.allow_private is True


class TestApiConfig:
    def test_default_values(self) -> None:
        cfg = ApiConfig()
        assert cfg.bind_host == "127.0.0.1"
        assert cfg.port == 8000
        assert cfg.api_key is None
        assert cfg.max_concurrent_scans == 3
        assert cfg.per_client_rpm == 10
        assert cfg.db_path == "sitesentry.db"

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SITESENTRY_API_PORT", "9000")
        monkeypatch.setenv("SITESENTRY_API_BIND_HOST", "0.0.0.0")
        monkeypatch.setenv("SITESENTRY_API_KEY", "supersecret")
        cfg = ApiConfig()
        assert cfg.port == 9000
        assert cfg.bind_host == "0.0.0.0"
        assert cfg.api_key == "supersecret"
