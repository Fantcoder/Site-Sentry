# SiteSentry

**Passive, safe-by-default web security auditing in Python.**

[![CI](https://github.com/Fantcoder/Site-Sentry/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Fantcoder/Site-Sentry/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SiteSentry crawls a target website within its registrable origin and executes 16 **passive** security evaluations without sending attack payloads, injection vectors, or fuzzing data. Every finding contains an assigned severity, captured evidence, a clear explanation, and specific remediation advice.

The engine produces an explainable grade (**A** through **F**) and exports reports in **JSON**, **Markdown**, self-contained **HTML** (zero CDN dependencies), and **SARIF 2.1.0** (for native GitHub Code Scanning integration). Both a Typer CLI and an async FastAPI service share the identical underlying scanning engine.

---

## ⚠️ Safety & Responsible Use Notice

> [!IMPORTANT]
> SiteSentry is built strictly for authorized security auditing of web assets you own or have explicit written permission to test.
>
> 1. **Permission Gate:** The scanner refuses execution unless `--i-have-permission` (CLI) or `"confirm_permission": true` (API) is supplied.
> 2. **Strict Scope Guard:** Only the target registrable origin is crawled; cross-origin links are reported, not followed.
> 3. **SSRF Guard:** Refuses loopback, RFC 1918 private ranges, link-local metadata (`169.254.169.254`), decimal (`http://2130706433`), octal (`http://0177.0.0.1`), and IPv6 addresses at connect time across every redirect hop.
> 4. **No Secrets in Output:** If sensitive files (`.env`, `/.git/HEAD`) are detected, SiteSentry logs existence, status code, and byte size only. **It never stores, parses, or prints sensitive file contents.**
> 5. **Polite by Default:** Enforces rate limiting (default 2 req/s), bounds crawling to max 50 pages and depth 2, caps response size at 1 MB, and respects `robots.txt`.

---

## 🚀 Quickstart

### Installation

Clone and install using [uv](https://github.com/astral-sh/uv) or pip:

```bash
git clone https://github.com/Fantcoder/Site-Sentry.git
cd Site-Sentry
uv sync
```

### CLI Usage

```bash
# Basic scan (permission flag is mandatory)
uv run sitesentry scan https://example.com --i-have-permission

# Export self-contained HTML report with CI threshold
uv run sitesentry scan https://example.com --i-have-permission --format html --output report.html --fail-on high

# Export SARIF for GitHub code scanning
uv run sitesentry scan https://example.com --i-have-permission --format sarif --output results.sarif

# List all 16 registered passive checks
uv run sitesentry checks
```

#### Exit Codes (CI/CD Gating)
- `0`: Scan passed (no findings meeting or exceeding `--fail-on`).
- `1`: Tool or configuration error.
- `2`: Findings detected at or above `--fail-on` severity threshold.

---

## 🌐 REST API Service

Launch the FastAPI service:

```bash
uv run sitesentry serve --host 127.0.0.1 --port 8000
```


### Web Dashboard

The FastAPI service also serves a browser-based dashboard at **http://127.0.0.1:8000/**.

The dashboard lets you:
- Submit an authorized scan with configurable page and crawl-depth limits.
- Watch pending/running scans refresh automatically.
- Review the grade, score, pages scanned, findings, evidence, and remediation advice.
- Browse recent scan history.
- Download HTML, Markdown, JSON, or SARIF reports.

Start the service, then open the dashboard in your browser:

```bash
uv run sitesentry serve --host 127.0.0.1 --port 8000
```

Keep the service bound to localhost while experimenting. When an API key is configured with `SITESENTRY_API_KEY`, paste it into the dashboard's API key field; the dashboard uses the existing authenticated API endpoints. Do not expose the service publicly without authentication and suitable network protections.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/scans` | Submit background scan. Requires `"confirm_permission": true`. |
| `GET` | `/api/v1/scans/{id}` | Check status and retrieve scan results. |
| `GET` | `/api/v1/scans/{id}/report` | Retrieve report formatted as `json`, `md`, `html`, or `sarif`. |
| `GET` | `/health` | Liveness healthcheck (returns `{"status": "ok"}`). |
| `GET` | `/ready` | Readiness check verifying SQLite database connectivity. |

---

## 🔍 Passive Security Checks

| Check ID | Focus | Severity |
|---|---|---|
| `hdr-csp` | Content-Security-Policy presence & weak directives (`'unsafe-inline'`, wildcard `*`) | Medium / Low |
| `hdr-hsts` | Strict-Transport-Security presence, `max-age` >= 6 months, `includeSubDomains` | Medium / Low |
| `hdr-xfo` | Missing `X-Frame-Options` and CSP `frame-ancestors` (Clickjacking) | Low |
| `hdr-xcto` | Missing `X-Content-Type-Options: nosniff` (MIME sniffing) | Low |
| `hdr-referrer` | Missing `Referrer-Policy` (Information leakage) | Info |
| `hdr-permissions`| Missing `Permissions-Policy` (Browser feature restriction) | Info |
| `cookie-flags` | Missing `Secure`, `HttpOnly`, `SameSite` flags on cookies (session tokens ranked higher) | Medium / Low |
| `tls-cert` | Expired, approaching expiration (<14 / <30 days), self-signed, hostname mismatch | High / Med / Low |
| `tls-protocol` | Server accepts deprecated TLS 1.0 or TLS 1.1 handshakes | Medium |
| `redirect-https`| HTTP does not redirect to HTTPS | Medium |
| `cors-misconfig`| Reflected arbitrary Origin or `*` origin combined with `Allow-Credentials: true` | High / Medium |
| `exposed-files` | Fixed probe (`/.git/HEAD`, `/.env`, `/.DS_Store`, `/backup.zip`, `/phpinfo.php`, `security.txt`) | High / Med / Info |
| `tech-disclosure`| `Server`, `X-Powered-By`, or `<meta name="generator">` disclosing versions | Low / Info |
| `mixed-content` | Unencrypted HTTP subresources embedded inside HTTPS pages | Medium |
| `sri-missing` | External scripts or stylesheets loaded without `integrity` hashes | Low |
| `dir-listing` | Web server directory listings (`Index of /`, `[To Parent Directory]`) | Medium |

---

## 📊 Real Sample Report

The following report was generated by running `scripts/sample_output.py` against the in-process vulnerable test server fixture:

```markdown
# SiteSentry Scan Report

| Field | Value |
|---|---|
| Target | `http://127.0.0.1:59205` |
| Scan ID | `3749f629-796f-4db4-8d2f-f0a29208fcba` |
| Started | 2026-11-02 13:10:10 UTC |
| Completed | 2026-11-02 13:10:11 UTC |
| Pages Crawled | 5 |
| **Grade** | **F** |
| **Score** | **30/100** |

## Score Breakdown

| Check | Findings | Deduction |
|---|---|---|
| hdr-csp | 1 | -7 |
| hdr-hsts | 0 | -0 |
| hdr-xfo | 1 | -3 |
| hdr-xcto | 1 | -3 |
| hdr-referrer | 1 | -0 |
| hdr-permissions | 1 | -0 |
| cookie-flags | 1 | -7 |
| tls-cert | 0 | -0 |
| tls-protocol | 0 | -0 |
| redirect-https | 1 | -7 |
| cors-misconfig | 0 | -0 |
| exposed-files | 5 | -30 |
| tech-disclosure | 2 | -6 |
| mixed-content | 0 | -0 |
| sri-missing | 0 | -0 |
| dir-listing | 1 | -7 |

## Findings

### 🔴 High (3)

#### [exposed-files] .git/HEAD exposed
- **URL:** `http://127.0.0.1:59205/.git/HEAD`
- **Evidence:** `HTTP 200, size=21 bytes, body starts with 'ref: refs/heads/main\n'`
- **Explanation:** Git repository HEAD file is publicly accessible
- **Fix:** Remove or restrict access to /.git/HEAD. Ensure your web server does not serve sensitive files.

#### [exposed-files] .env file exposed
- **URL:** `http://127.0.0.1:59205/.env`
- **Evidence:** `HTTP 200, size=37 bytes`
- **Explanation:** .env environment file is publicly accessible
- **Fix:** Remove or restrict access to /.env. Ensure your web server does not serve sensitive files.
```

---

## ⚙️ Configuration Reference

### Scan Options (`ScanConfig`)

| Field | Type | Default | Description |
|---|---|---|---|
| `target_url` | `str` | `""` | Target URL to scan |
| `confirm_permission` | `bool` | `False` | Must be True to run a scan. Confirms you own/are authorised to test the target. |
| `max_pages` | `int` | `50` | Maximum pages to crawl |
| `max_depth` | `int` | `2` | Maximum crawl depth |
| `rate_limit` | `float` | `2.0` | Requests per second (politeness) |
| `request_timeout` | `float` | `10.0` | Per-request timeout in seconds |
| `scan_timeout` | `float` | `120.0` | Global scan timeout in seconds |
| `max_response_size` | `int` | `1048576` | Maximum bytes to read per response (1 MB) |
| `allow_private` | `bool` | `False` | Allow scanning private/loopback IPs (disable SSRF guard). Local testing only. |
| `respect_robots` | `bool` | `True` | Respect robots.txt disallow rules |
| `ignore_robots` | `bool` | `False` | Ignore robots.txt (opt-in override of respect_robots) |
| `output_format` | `OutputFormat` | `json` | Report output format (`json`, `md`, `html`, `sarif`) |
| `output_file` | `str | None` | `None` | Write report to this file instead of stdout |
| `fail_on` | `Severity` | `high` | Exit code 2 if any finding at or above this severity |

### API Service Options (`ApiConfig`)

| Field | Type | Default | Description |
|---|---|---|---|
| `bind_host` | `str` | `127.0.0.1` | Host to bind API server to (set 0.0.0.0 in Docker). |
| `port` | `int` | `8000` | Port to listen on. |
| `api_key` | `str | None` | `None` | Optional Bearer token for scan endpoints. Compare with hmac.compare_digest. |
| `max_concurrent_scans` | `int` | `3` | Maximum number of simultaneous background scans |
| `per_client_rpm` | `int` | `10` | Maximum scan requests per client per minute |
| `db_path` | `str` | `sitesentry.db` | SQLite database file path |

---

## 🐳 Docker Deployment

A multi-stage non-root Docker image is provided:

```bash
docker build -t sitesentry .
docker run -p 8000:8000 sitesentry
```

---

## 🧪 Testing & Verification

```bash
# Run full test suite with coverage
uv run pytest --cov=sitesentry --cov-report=term-missing

# Run strict type checking
uv run mypy

# Run security linting
uv run bandit -r src/

# Run format and lint checks
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

See [VERIFICATION.md](VERIFICATION.md) for full gate execution logs.
