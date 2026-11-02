# SiteSentry Scoring Engine

This document specifies the algorithm, severity weights, deduction caps, and grading thresholds used by SiteSentry.

> [!NOTE]
> The weights, deduction caps, and grade boundaries defined below are **heuristics** designed to provide an actionable, explainable security health score. They do not constitute formal compliance ratings.

---

## 1. Severity Weights

Each unique finding incurs a score deduction based on its assigned severity:

| Severity | Deduction Weight | Rationale |
|---|---|---|
| **Critical** | `25` | Direct vulnerability that permits unauthorized access or compromise. |
| **High** | `15` | Critical file exposure, arbitrary CORS credential reflection, or invalid TLS certificate. |
| **Medium** | `7` | Missing foundational security controls (CSP, HSTS, Secure cookies, outdated TLS 1.0/1.1). |
| **Low** | `3` | Defense-in-depth gaps (missing XFO, nosniff, SRI on external scripts, weak CSP directives). |
| **Info** | `0` | Observational metadata (missing security.txt, technology version disclosure). |

---

## 2. Deduction Caps & De-duplication

To avoid disproportionate penalties from noisy checks (e.g., a site with dozens of identical cookies missing the `SameSite` attribute), two normalization mechanisms are applied:

1. **Finding De-duplication:**  
   Findings are de-duplicated by their computed `dedupe_key = sha256(f"{check_id}:{evidence}")[:16]`. A recurring issue observed across multiple crawled pages is counted only once in the score calculation.
2. **Per-Check Deduction Cap:**  
   The total deduction contributed by any single check ID is capped at `MAX_DEDUCTION_PER_CHECK = 30`. This guarantees that a single noisy check cannot reduce the site score below 70.

Formula:
$$\text{CheckDeduction} = \min\left(30, \sum_{f \in \text{UniqueFindings}} \text{Weight}(f.\text{severity})\right)$$
$$\text{Score} = \max\left(0, 100 - \sum_{\text{check}} \text{CheckDeduction}\right)$$

---

## 3. Grading Thresholds & Hard Caps

Base grades are assigned according to the final score:

| Score Range | Base Grade |
|---|---|
| 90 – 100 | **A** |
| 80 – 89 | **B** |
| 70 – 79 | **C** |
| 60 – 69 | **D** |
| 0 – 59 | **F** |

### Hard-Cap Safety Rules
1. **High / Critical Severity Cap:** If any finding has a severity of `high` or `critical`, the maximum achievable grade is **C**. A site exposing an unauthenticated `.env` or `.git/HEAD` file can never receive an A or B, regardless of its numeric score.
2. **Incomplete Check Penalty:** If any check encounters an unhandled runtime error or timeout, the scan is flagged with `has_incomplete_checks = True`. In this scenario, the grade is downgraded (cannot be A) to avoid giving false assurance.

---

## 4. Worked Examples (Computed Directly from Real Code)

The following examples were generated directly using `sitesentry.scoring.compute_score`:

### Example 1: Hardened, Clean Site
- **Findings:** None.
- **Score:** `100`
- **Grade:** **`A`**
- **Breakdown:** 0 deductions across all checks.

### Example 2: Typical Missing Security Headers
- **Findings:**
  - `hdr-csp` (Medium): Content-Security-Policy missing (-7)
  - `hdr-xfo` (Low): X-Frame-Options missing (-3)
  - `hdr-xcto` (Low): X-Content-Type-Options missing (-3)
- **Score:** `100 - (7 + 3 + 3) = 87`
- **Grade:** **`B`** (Score 87 falls within 80-89; no high severity findings present).

### Example 3: Site with Exposed Environment File
- **Findings:**
  - `exposed-files` (High): `.env file exposed` (-15)
  - `hdr-xfo` (Low): X-Frame-Options missing (-3)
- **Score:** `100 - (15 + 3) = 82`
- **Grade:** **`C`** (Although numeric score 82 would qualify for B, the hard-cap rule limits any scan with High severity findings to grade C).

### Example 4: Single Noisy Check Cap
- **Findings:**
  - `cookie-flags`: 10 unique cookies missing security attributes (10 × 7 = 70 raw deduction).
- **Capped Deduction:** `min(70, 30) = 30`
- **Score:** `100 - 30 = 70`
- **Grade:** **`C`** (The 30-point check cap prevented one check from reducing the score to 30).
