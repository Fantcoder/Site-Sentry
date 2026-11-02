# Changelog

All notable changes to **SiteSentry** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-02

### Added
- **Core Architecture:**
  - Asynchronous core built on Python 3.11+, `httpx`, `pydantic` v2, and `pydantic-settings`.
  - Permission gate: scans refuse execution without `--i-have-permission` (CLI) or `"confirm_permission": true` (API).
- **Security & Safety Guardrails:**
  - `ScopeGuard`: Strict registrable-origin scope enforcement preventing out-of-domain traversal.
  - Multi-layered SSRF defense: blocks loopback, RFC 1918, link-local metadata (`169.254.169.254`), decimal (`http://2130706433`), octal (`http://0177.0.0.1`), and IPv6 representations with DNS re-check on every redirect hop.
  - Zero secret leakage: discovered sensitive files (`.env`, `/.git/HEAD`) log status codes and content lengths only, never raw contents.
- **Polite Crawler:**
  - Breadth-first crawl bounded by depth (default 2) and pages (default 50).
  - Configurable rate limiting (default 2.0 req/s) with monotonic timing.
  - Automatic `robots.txt` disallow enforcement (with opt-in `--ignore-robots`).
  - Pre-crawl soft-404 detection baseline to eliminate false positive reports.
- **Passive Security Checks:**
  - 16 dedicated check modules covering CSP, HSTS, XFO, XCTO, Referrer-Policy, Permissions-Policy, Cookie flags, TLS certificate validity and expiration, legacy TLS 1.0/1.1 protocols, HTTP-to-HTTPS redirect, CORS reflection, sensitive file exposure, technology disclosure, mixed content, Subresource Integrity (SRI), and directory listing.
  - Crash isolation: individual check errors are captured as incomplete without aborting the overall scan.
- **Scoring & Grading Engine:**
  - Weighted deductions: Critical (25), High (15), Medium (7), Low (3), Info (0).
  - Per-check deduction cap of 30 points to prevent skew from noisy endpoints.
  - Deterministic grading (A >= 90, B >= 80, C >= 70, D >= 60, F < 60) with safety hard caps limiting grade to C upon any High or Critical finding.
- **Multi-Format Reporting:**
  - Output formats for JSON, Markdown, self-contained HTML (zero external CDN scripts), and SARIF 2.1.0 validated against OASIS schema.
- **Interfaces:**
  - Typer CLI with Rich terminal output, check discovery, and CI exit-code gating (`--fail-on`).
  - FastAPI asynchronous service with bounded background worker pool, sliding-window rate limiter, and constant-time API key verification.
- **Persistence:**
  - SQLite storage with write-ahead logging (WAL) via `aiosqlite`.
- **Quality & Testing:**
  - 196 automated tests with >90% code coverage.
  - Local in-process vulnerable server fixture for deterministic integration testing.
  - Full static analysis pass: `ruff` (lint & format), `mypy --strict`, `bandit` (0 issues).
