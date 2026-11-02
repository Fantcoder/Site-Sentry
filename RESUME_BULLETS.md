# Resume Bullets — SiteSentry

These bullet points are strictly derived from verified output and benchmark commands. Each quantitative metric lists the exact command used to produce it.

---

### Backend / Security Tooling Bullets

- **Engineered an asynchronous passive web security scanner in Python 3.11** using `httpx`, `asyncio`, and `BeautifulSoup4`, implementing 16 passive security checks (headers, cookies, TLS certificates, CORS reflection, sensitive files) without transmitting active attack payloads.  
  *Command: `uv run sitesentry checks` (16 registered checks)*

- **Architected multi-layered SSRF defenses and scope guardrails** that resolve and block loopback, RFC 1918, link-local metadata (`169.254.169.254`), decimal (`2130706433`), and octal IP encodings at connect time across all redirect hops before requests are dispatched.  
  *Command: `uv run pytest tests/unit/test_scope.py` (32 passed tests including property-based fuzzing with Hypothesis)*

- **Achieved 90.82% test coverage across 196 automated tests** using `pytest`, `pytest-asyncio`, `respx`, and `Hypothesis`, validating crash isolation, scoring thresholds, and local end-to-end integration against an in-process misconfigured test server.  
  *Command: `uv run pytest --cov=sitesentry --cov-report=term-missing` (196 passed, 90.82% total coverage)*

- **Enforced strict code quality and security standards** with 0 type errors under `mypy --strict` across 28 source files and 0 security issues flagged by `bandit` across 3,017 lines of application code.  
  *Commands: `uv run mypy` (Success: no issues found in 28 source files); `uv run bandit -r src/` (No issues identified across 3,017 LOC)*

- **Benchmarked crawler throughput at 5.35 pages/second** with configurable token-bucket rate limiting, automatic `robots.txt` disallow enforcement, and soft-404 signature baselining to eliminate false positive file exposures.  
  *Command: `uv run python scripts/bench_scan.py` (5.35 p/s at 20 req/s, 14 requests completed in 0.93s)*

- **Built unified CLI and REST API services** using `Typer` with exit code CI gating and `FastAPI` with bounded background scan pools, sliding-window per-client rate limiting, and multi-format reporting (JSON, Markdown, standalone HTML, and SARIF 2.1.0).  
  *Command: `uv run pytest tests/unit/test_cli.py tests/unit/test_api.py tests/unit/test_report.py` (37 passed tests)*
