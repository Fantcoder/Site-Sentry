"""Cookie security flags check."""

from __future__ import annotations

import re

from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

# Cookies whose names suggest they are session / auth related
_SESSION_PATTERN = re.compile(
    r"session|sess|sid|token|auth|jwt|csrf|xsrf|login|user|uid|account",
    re.IGNORECASE,
)


def _parse_set_cookie(header_value: str) -> dict[str, str]:
    """Parse a Set-Cookie header into a dict of attributes (lowercase keys)."""
    parts = [p.strip() for p in header_value.split(";")]
    attrs: dict[str, str] = {}
    if parts:
        name_val = parts[0]
        if "=" in name_val:
            name, _, val = name_val.partition("=")
            attrs["_name"] = name.strip()
            attrs["_value"] = val.strip()
        else:
            attrs["_name"] = name_val
            attrs["_value"] = ""
    for part in parts[1:]:
        if "=" in part:
            k, _, v = part.partition("=")
            attrs[k.strip().lower()] = v.strip()
        else:
            attrs[part.strip().lower()] = ""
    return attrs


class CookieFlagsCheck(BaseCheck):
    id = "cookie-flags"
    title = "Cookie Security Flags"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []

        for page in context.pages:
            if page.status_code >= 400:
                continue

            # httpx lowercases header names; cookies may come as a list
            # We collect all Set-Cookie values from the raw header dict
            # httpx merges multiple Set-Cookie into a comma-joined string if same key
            # So we use the raw response; here we stored headers as dict[str, str]
            raw_cookies: list[str] = []
            for key, val in page.headers.items():
                if key.lower() == "set-cookie":
                    # Multiple set-cookie headers may be merged with newlines by httpx
                    raw_cookies.extend(val.split("\n"))

            for cookie_raw in raw_cookies:
                cookie_raw = cookie_raw.strip()
                if not cookie_raw:
                    continue

                attrs = _parse_set_cookie(cookie_raw)
                name = attrs.get("_name", "unknown")
                is_session = bool(_SESSION_PATTERN.search(name))
                base_severity = Severity.medium if is_session else Severity.low

                # Check Secure flag (only meaningful for HTTPS pages)
                if page.is_https and "secure" not in attrs:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"Cookie '{name}' missing Secure flag",
                            severity=base_severity,
                            url=page.url,
                            evidence=f"Set-Cookie: {name}=... (Secure absent)",
                            explanation=(
                                f"The cookie '{name}' is set without the Secure flag. "
                                "It can be transmitted over unencrypted HTTP connections, "
                                "exposing it to network interception."
                            ),
                            fix=(
                                f"Add the Secure flag to the '{name}' cookie: "
                                "Set-Cookie: name=value; Secure; ..."
                            ),
                        )
                    )

                # Check HttpOnly flag
                if "httponly" not in attrs:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"Cookie '{name}' missing HttpOnly flag",
                            severity=base_severity,
                            url=page.url,
                            evidence=f"Set-Cookie: {name}=... (HttpOnly absent)",
                            explanation=(
                                f"The cookie '{name}' is accessible to JavaScript. "
                                "If the site has an XSS vulnerability, an attacker can "
                                "steal this cookie."
                            ),
                            fix=("Add the HttpOnly flag: Set-Cookie: name=value; HttpOnly; ..."),
                        )
                    )

                # Check SameSite flag
                samesite = attrs.get("samesite", "")
                if not samesite:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"Cookie '{name}' missing SameSite attribute",
                            severity=base_severity,
                            url=page.url,
                            evidence=f"Set-Cookie: {name}=... (SameSite absent)",
                            explanation=(
                                f"The cookie '{name}' has no SameSite attribute. "
                                "Without SameSite, the cookie is sent with cross-site "
                                "requests, which can enable CSRF attacks."
                            ),
                            fix=(
                                "Add SameSite=Lax (or Strict for sensitive cookies): "
                                "Set-Cookie: name=value; SameSite=Lax"
                            ),
                        )
                    )
                elif samesite.lower() == "none" and "secure" not in attrs:
                    findings.append(
                        Finding(
                            check_id=self.id,
                            title=f"Cookie '{name}' has SameSite=None without Secure",
                            severity=Severity.medium,
                            url=page.url,
                            evidence=f"Set-Cookie: {name}=... (SameSite=None; Secure absent)",
                            explanation=(
                                "SameSite=None requires the Secure flag. Without it, "
                                "modern browsers will reject the cookie entirely."
                            ),
                            fix="Add the Secure flag when using SameSite=None.",
                        )
                    )

        return findings
