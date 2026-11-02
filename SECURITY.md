# Security Policy & Responsible Use

## 1. Responsible Use Policy

SiteSentry is an automated **passive** web security assessment tool designed strictly for authorized security auditing, defensive hardening, and educational research.

### Authorized Testing Only
- You **MUST** obtain explicit written authorization before scanning any target infrastructure you do not own.
- The CLI enforces this via the mandatory `--i-have-permission` flag.
- The API enforces this via `"confirm_permission": true` on scan creation requests.

### What SiteSentry Does NOT Do
SiteSentry is deliberately engineered as a safe-by-default, passive scanner:
- ❌ **No Exploitation:** Does not transmit injection payloads, SQLi, XSS, or remote code execution vectors.
- ❌ **No Brute-Forcing:** Does not perform password guessing, credential stuffing, or aggressive directory fuzzing.
- ❌ **No Denial of Service:** Operates with polite rate limits (default 2 req/s) and bounded page counts (default 50 pages).
- ❌ **No Secret Logging:** When sensitive files (such as `.env` or `/.git/HEAD`) are detected, SiteSentry logs only HTTP status metadata and response size. **It never stores, parses, or exposes the file contents.**

---

## 2. Reporting a Vulnerability in SiteSentry

If you identify a security vulnerability in SiteSentry itself (e.g., an SSRF bypass or denial-of-service vector), please report it responsibly:

1. **Email:** Send details to `security@sitesentry.invalid` or open a private GitHub Security Advisory.
2. **Details:** Include a clear description of the vulnerability, reproduction steps, and potential impact.
3. **Response Timeline:** We aim to acknowledge reports within 48 hours and provide a remediation plan within 5 business days.
4. **Coordinated Disclosure:** Please allow sufficient time for fixes to be merged before disclosing publicly.
