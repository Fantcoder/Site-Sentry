"""Security header checks: CSP, HSTS, XFO, XCTO, Referrer-Policy, Permissions-Policy."""

from __future__ import annotations

import re

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CSP_UNSAFE = re.compile(r"'unsafe-inline'|'unsafe-eval'", re.IGNORECASE)
_CSP_WILDCARD = re.compile(r"(?:^|[\s;])\*(?:[\s;]|$)")


def _make_finding(
    check_id: str,
    title: str,
    severity: Severity,
    url: str,
    evidence: str,
    explanation: str,
    fix: str,
) -> Finding:
    return Finding(
        check_id=check_id,
        title=title,
        severity=severity,
        url=url,
        evidence=evidence,
        explanation=explanation,
        fix=fix,
    )


# ---------------------------------------------------------------------------
# CSP
# ---------------------------------------------------------------------------


class CspCheck(BaseCheck):
    id = "hdr-csp"
    title = "Content-Security-Policy"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if page.status_code >= 400:
                continue
            csp = page.get_header("content-security-policy")
            if not csp:
                findings.append(
                    _make_finding(
                        self.id,
                        "Content-Security-Policy header missing",
                        Severity.medium,
                        page.url,
                        "Header not present",
                        "Without a CSP, browsers cannot restrict which scripts, styles, or "
                        "resources the page may load, making XSS attacks more impactful.",
                        "Add a Content-Security-Policy header. Start with "
                        "Content-Security-Policy: default-src 'self' and progressively "
                        "tighten it.",
                    )
                )
            else:
                # Check for unsafe directives
                if _CSP_UNSAFE.search(csp):
                    findings.append(
                        _make_finding(
                            self.id,
                            "CSP contains unsafe-inline or unsafe-eval",
                            Severity.low,
                            page.url,
                            csp[:200],
                            "'unsafe-inline' and 'unsafe-eval' defeat most XSS protections "
                            "provided by CSP.",
                            "Remove 'unsafe-inline' and 'unsafe-eval'. Use nonces or hashes "
                            "for inline scripts/styles.",
                        )
                    )
                if _CSP_WILDCARD.search(csp):
                    findings.append(
                        _make_finding(
                            self.id,
                            "CSP contains wildcard source (*)",
                            Severity.low,
                            page.url,
                            csp[:200],
                            "A wildcard (*) in the CSP source list allows loading resources "
                            "from any origin, negating the protection.",
                            "Replace * with specific trusted hostnames.",
                        )
                    )
        return findings


# ---------------------------------------------------------------------------
# HSTS
# ---------------------------------------------------------------------------

_HSTS_MAX_AGE_RE = re.compile(r"max-age=(\d+)", re.IGNORECASE)
_SIX_MONTHS_SECONDS = 15_768_000  # 6 × 30 × 24 × 3600


class HstsCheck(BaseCheck):
    id = "hdr-hsts"
    title = "HTTP Strict Transport Security"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if not page.is_https or page.status_code >= 400:
                continue  # HSTS is only meaningful on HTTPS
            hsts = page.get_header("strict-transport-security")
            if not hsts:
                findings.append(
                    _make_finding(
                        self.id,
                        "Strict-Transport-Security header missing",
                        Severity.medium,
                        page.url,
                        "Header not present",
                        "Without HSTS, browsers may access the site over plain HTTP, "
                        "exposing it to SSL-stripping attacks.",
                        "Add: Strict-Transport-Security: max-age=31536000; "
                        "includeSubDomains; preload",
                    )
                )
            else:
                m = _HSTS_MAX_AGE_RE.search(hsts)
                if not m:
                    findings.append(
                        _make_finding(
                            self.id,
                            "HSTS header missing max-age",
                            Severity.medium,
                            page.url,
                            hsts[:200],
                            "A Strict-Transport-Security header without max-age is invalid "
                            "and ignored by browsers.",
                            "Include max-age=31536000 (one year) in the HSTS header.",
                        )
                    )
                elif int(m.group(1)) < _SIX_MONTHS_SECONDS:
                    findings.append(
                        _make_finding(
                            self.id,
                            "HSTS max-age is less than 6 months",
                            Severity.low,
                            page.url,
                            hsts[:200],
                            f"max-age={m.group(1)} ({int(m.group(1)) // 86400} days). "
                            "Short max-age reduces HSTS protection effectiveness.",
                            "Set max-age to at least 15768000 (6 months); "
                            "31536000 (1 year) is recommended.",
                        )
                    )
                if "includesubdomains" not in hsts.lower():
                    findings.append(
                        _make_finding(
                            self.id,
                            "HSTS header missing includeSubDomains",
                            Severity.low,
                            page.url,
                            hsts[:200],
                            "Without includeSubDomains, subdomains of this origin are not "
                            "covered by HSTS and may be attacked via HTTP.",
                            "Add includeSubDomains to the Strict-Transport-Security header.",
                        )
                    )
        return findings


# ---------------------------------------------------------------------------
# X-Frame-Options
# ---------------------------------------------------------------------------


class XfoCheck(BaseCheck):
    id = "hdr-xfo"
    title = "X-Frame-Options / frame-ancestors"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if page.status_code >= 400:
                continue
            xfo = page.get_header("x-frame-options")
            csp = page.get_header("content-security-policy")
            has_frame_ancestors = csp and "frame-ancestors" in csp.lower()
            if not xfo and not has_frame_ancestors:
                findings.append(
                    _make_finding(
                        self.id,
                        "X-Frame-Options or CSP frame-ancestors missing",
                        Severity.low,
                        page.url,
                        "X-Frame-Options: absent; CSP frame-ancestors: absent",
                        "Without framing protection, this page can be embedded in an "
                        "attacker-controlled iframe, enabling clickjacking attacks.",
                        "Add X-Frame-Options: DENY (or SAMEORIGIN), or add "
                        "frame-ancestors 'self' to your Content-Security-Policy.",
                    )
                )
        return findings


# ---------------------------------------------------------------------------
# X-Content-Type-Options
# ---------------------------------------------------------------------------


class XctoCheck(BaseCheck):
    id = "hdr-xcto"
    title = "X-Content-Type-Options"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if page.status_code >= 400:
                continue
            xcto = page.get_header("x-content-type-options")
            if xcto.lower().strip() != "nosniff":
                findings.append(
                    _make_finding(
                        self.id,
                        "X-Content-Type-Options: nosniff missing",
                        Severity.low,
                        page.url,
                        f"X-Content-Type-Options: {xcto!r}" if xcto else "Header not present",
                        "Without nosniff, some browsers may MIME-sniff responses and "
                        "execute content as a different type than declared (e.g., execute "
                        "a JSONP endpoint as a script).",
                        "Add: X-Content-Type-Options: nosniff",
                    )
                )
        return findings


# ---------------------------------------------------------------------------
# Referrer-Policy
# ---------------------------------------------------------------------------


class ReferrerPolicyCheck(BaseCheck):
    id = "hdr-referrer"
    title = "Referrer-Policy"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if page.status_code >= 400:
                continue
            rp = page.get_header("referrer-policy")
            if not rp:
                findings.append(
                    _make_finding(
                        self.id,
                        "Referrer-Policy header missing",
                        Severity.info,
                        page.url,
                        "Header not present",
                        "Without Referrer-Policy, the browser's default behaviour may leak "
                        "full URLs (including query parameters with sensitive data) to "
                        "third-party sites via the Referer header.",
                        "Add: Referrer-Policy: strict-origin-when-cross-origin",
                    )
                )
        return findings


# ---------------------------------------------------------------------------
# Permissions-Policy
# ---------------------------------------------------------------------------


class PermissionsPolicyCheck(BaseCheck):
    id = "hdr-permissions"
    title = "Permissions-Policy"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for page in context.pages:
            if page.status_code >= 400:
                continue
            pp = page.get_header("permissions-policy")
            if not pp:
                findings.append(
                    _make_finding(
                        self.id,
                        "Permissions-Policy header missing",
                        Severity.info,
                        page.url,
                        "Header not present",
                        "Without Permissions-Policy (formerly Feature-Policy), powerful "
                        "browser features (camera, microphone, geolocation) may be "
                        "accessible to embedded third-party iframes.",
                        "Add a Permissions-Policy header to restrict which browser features "
                        "this page and its embedded content may use.",
                    )
                )
        return findings
