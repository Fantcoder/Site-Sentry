# Verification Report — SiteSentry

**Date:** 2026-11-02  
**Environment:** Windows (win32), Python 3.11.9, uv 0.10.9  
**Repository:** https://github.com/Fantcoder/Site-Sentry.git  
**Default Branch:** `main`

---

## 1. Quality & Security Gates Executed

### 1.1 Code Formatting (`ruff format`)
**Command:** `uv run ruff format --check src/ tests/`  
**Result:** Passed (0 errors, 53 files inspected).
```text
53 files already formatted
```

### 1.2 Code Linting (`ruff check`)
**Command:** `uv run ruff check src/ tests/`  
**Result:** Passed (0 errors).
```text
All checks passed!
```

### 1.3 Static Type Checking (`mypy --strict`)
**Command:** `uv run mypy`  
**Configuration:** `strict = true`, `python_version = "3.11"`, `plugins = ["pydantic.mypy"]`  
**Result:** Passed (0 errors across 28 source files).
```text
Success: no issues found in 28 source files
```

### 1.4 Security Static Analysis (`bandit`)
**Command:** `uv run bandit -r src/`  
**Result:** Passed (0 issues found).
```text
Code scanned:
	Total lines of code: 3017
	Total lines skipped (#nosec): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
```

### 1.5 Automated Test Suite & Code Coverage (`pytest`)
**Command:** `uv run pytest --cov=sitesentry --cov-report=term-missing`  
**Result:** **196 passed**, 0 failed. Total coverage: **90.82%** (satisfies requirement `>= 90.0%`).
```text
Name                                         Stmts   Miss Branch BrPart  Cover   Missing
----------------------------------------------------------------------------------------
src\sitesentry\__init__.py                       2      0      0      0   100%
src\sitesentry\aggregator.py                    86      3      8      0    97%   74-76
src\sitesentry\api\__init__.py                   0      0      0      0   100%
src\sitesentry\api\app.py                       33      0      2      0   100%
src\sitesentry\api\auth.py                      12      0      6      0   100%
src\sitesentry\api\ratelimit.py                 24      2      4      1    89%   38, 54
src\sitesentry\api\routes.py                   102     11     18      3    88%   92-93, 180-185, 207, 226, 249
src\sitesentry\checks\__init__.py                0      0      0      0   100%
src\sitesentry\checks\base.py                   26      3      6      3    81%   38, 43->exit, 45, 47
src\sitesentry\checks\cookies.py                52      3     28      3    92%   21->30, 28-29, 63
src\sitesentry\checks\cors.py                   30      3      6      1    89%   38-40, 74->106
src\sitesentry\checks\directory_listing.py      18      1      8      1    92%   29
src\sitesentry\checks\exposed_files.py          57      5     12      0    93%   150-152, 158-159
src\sitesentry\checks\headers.py                95      5     46      5    93%   135, 190, 224, 256, 288
src\sitesentry\checks\mixed_content.py          26      0     12      0   100%
src\sitesentry\checks\redirect.py               32      4      8      1    88%   51, 101-103
src\sitesentry\checks\registry.py               18      1      0      0    94%   49
src\sitesentry\checks\sri.py                    40      6     24      6    81%   31, 64, 66, 70, 72, 74
src\sitesentry\checks\tech_disclosure.py        33      1     18      4    90%   37, 68->40, 87->35, 91->89
src\sitesentry\checks\tls.py                    99     14     28      5    85%   29-32, 34, 36, 49-50, 57-58, 102-103, 107, 111->161, 146
src\sitesentry\cli.py                           81     14     18      2    78%   118-120, 126-133, 154, 202-204
src\sitesentry\config.py                        40      1      2      1    95%   81
src\sitesentry\crawler.py                      180     17     50      9    89%   72, 107->exit, 135->139, 152, 168, 225, 238-242, 249-254, 260-261, 309-310, 336->340
src\sitesentry\models.py                       124      1     16      1    99%   134
src\sitesentry\report.py                        92      0     28      0   100%
src\sitesentry\scope.py                        127     16     50      5    85%   68, 103-104, 118, 129-131, 153->158, 160->166, 171-184, 219, 258
src\sitesentry\scoring.py                       34      0     16      0   100%
src\sitesentry\storage.py                       57      2      6      2    94%   50, 111
----------------------------------------------------------------------------------------
TOTAL                                         1520    113    420     53    91%

Required test coverage of 90.0% reached. Total coverage: 90.82%
====================== 196 passed, 7 warnings in 29.15s =======================
```

### 1.6 Crawl Throughput Benchmark (`scripts/bench_scan.py`)
**Command:** `uv run python scripts/bench_scan.py`  
**Result:**
```text
| Rate Limit (req/s) | Total Duration (s) | Estimated Requests | Pages / Second |
|---|---|---|---|
|  1.0 |   6.68s |   14 |  0.75 p/s |
|  5.0 |   1.90s |   14 |  2.63 p/s |
| 20.0 |   0.93s |   14 |  5.35 p/s |
```

### 1.7 End-to-End Integration Scan (`scripts/sample_output.py`)
**Command:** `uv run python scripts/sample_output.py`  
**Result:**
```text
Generated sample reports in docs\samples:
  - docs\samples\sample_report.json
  - docs\samples\sample_report.md
  - docs\samples\sample_report.html
  - docs\samples\sample_report.sarif
Grade: F, Score: 30/100, Total Findings: 15
```

### 1.8 Remote GitHub Actions CI Execution
**Workflow Run:** [Run 41453873932](https://github.com/Fantcoder/Site-Sentry/actions/runs/41453873932)  
**Trigger Commit:** [`b8371ee`](https://github.com/Fantcoder/Site-Sentry/commit/b8371ee)  
**Status:** **Success (100% Passing)**
- **Test & Lint (Python 3.11):** Passed (Checkout, setup-uv, ruff, mypy, bandit, pip-audit, pytest)
- **Test & Lint (Python 3.12):** Passed (Checkout, setup-uv, ruff, mypy, bandit, pip-audit, pytest)

---

## 2. Explicit UNVERIFIED List

In accordance with engineering guidelines, the following items were not executed in this environment and remain explicitly unverified:

- [ ] **Docker image build & runtime execution:** Docker daemon is not available inside this development container.
- [ ] **Scanning third-party live domains:** All tests deliberately targeted the in-process vulnerable server and unit mocks to adhere to the non-negotiable safety rules.
- [ ] **Live TLS handshake against third-party public CAs:** TLS checks were verified using local mock sockets and unit test harnesses.
