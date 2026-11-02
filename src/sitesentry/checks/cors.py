"""CORS misconfiguration check.

Sends one request with a benign Origin header and inspects the response.
"""

from __future__ import annotations

import logging

import httpx

from sitesentry import __repo__, __version__
from sitesentry.checks.base import BaseCheck, ScanContext
from sitesentry.models import Finding, Severity

logger = logging.getLogger(__name__)

_PROBE_ORIGIN = "https://sitesentry.invalid"
USER_AGENT = f"SiteSentry/{__version__} (+{__repo__})"


class CorsMisconfigCheck(BaseCheck):
    id = "cors-misconfig"
    title = "CORS Misconfiguration"

    async def run(self, context: ScanContext) -> list[Finding]:
        target = context.target_url
        findings: list[Finding] = []

        try:
            resp = await context.http_client.get(
                target,
                headers={
                    "Origin": _PROBE_ORIGIN,
                    "User-Agent": USER_AGENT,
                },
            )
        except httpx.RequestError as exc:
            logger.debug("CORS probe request failed: %s", exc)
            return []

        acao = resp.headers.get("access-control-allow-origin", "")
        acac = resp.headers.get("access-control-allow-credentials", "").lower()

        if not acao:
            return []  # No CORS header at all – not a finding

        # Case 1: wildcard + credentials (high severity)
        if acao == "*" and acac == "true":
            findings.append(
                Finding(
                    check_id=self.id,
                    title="CORS: wildcard origin with Allow-Credentials",
                    severity=Severity.high,
                    url=target,
                    evidence=(
                        f"Access-Control-Allow-Origin: {acao}, "
                        f"Access-Control-Allow-Credentials: {acac}"
                    ),
                    explanation=(
                        "CORS is configured with Access-Control-Allow-Origin: * and "
                        "Access-Control-Allow-Credentials: true. While browsers do not "
                        "actually allow this combination, it indicates a misconfigured "
                        "CORS policy that may be exploitable in non-browser contexts."
                    ),
                    fix=(
                        "Never combine a wildcard origin with Allow-Credentials. "
                        "Use a specific allowlist of trusted origins instead."
                    ),
                )
            )

        # Case 2: reflects arbitrary origin
        elif acao == _PROBE_ORIGIN:
            severity = Severity.high if acac == "true" else Severity.medium
            findings.append(
                Finding(
                    check_id=self.id,
                    title="CORS reflects arbitrary Origin header",
                    severity=severity,
                    url=target,
                    evidence=(
                        f"Access-Control-Allow-Origin: {acao} "
                        f"(reflected probe origin {_PROBE_ORIGIN!r})"
                        + (f", Access-Control-Allow-Credentials: {acac}" if acac else "")
                    ),
                    explanation=(
                        "The server reflects any Origin header value in "
                        "Access-Control-Allow-Origin. This means any website can make "
                        "cross-origin requests to this API."
                        + (
                            " Combined with Allow-Credentials: true, an attacker can "
                            "make authenticated requests on behalf of a logged-in user."
                            if acac == "true"
                            else ""
                        )
                    ),
                    fix=(
                        "Maintain an explicit allowlist of trusted origins. "
                        "Validate the Origin header against the list and only reflect "
                        "it if it matches. Never use a request-controlled value directly."
                    ),
                )
            )

        return findings
