"""Check registry – imports and registers all check classes."""

from __future__ import annotations

from sitesentry.checks.base import BaseCheck
from sitesentry.checks.cookies import CookieFlagsCheck
from sitesentry.checks.cors import CorsMisconfigCheck
from sitesentry.checks.directory_listing import DirectoryListingCheck
from sitesentry.checks.exposed_files import ExposedFilesCheck
from sitesentry.checks.headers import (
    CspCheck,
    HstsCheck,
    PermissionsPolicyCheck,
    ReferrerPolicyCheck,
    XctoCheck,
    XfoCheck,
)
from sitesentry.checks.mixed_content import MixedContentCheck
from sitesentry.checks.redirect import HttpsRedirectCheck
from sitesentry.checks.sri import SriMissingCheck
from sitesentry.checks.tech_disclosure import TechDisclosureCheck
from sitesentry.checks.tls import TlsCertCheck, TlsProtocolCheck

# Ordered list of all check classes
ALL_CHECKS: list[type[BaseCheck]] = [
    CspCheck,
    HstsCheck,
    XfoCheck,
    XctoCheck,
    ReferrerPolicyCheck,
    PermissionsPolicyCheck,
    CookieFlagsCheck,
    TlsCertCheck,
    TlsProtocolCheck,
    HttpsRedirectCheck,
    CorsMisconfigCheck,
    ExposedFilesCheck,
    TechDisclosureCheck,
    MixedContentCheck,
    SriMissingCheck,
    DirectoryListingCheck,
]

_CHECK_MAP: dict[str, type[BaseCheck]] = {cls.id: cls for cls in ALL_CHECKS}


def get_check(check_id: str) -> type[BaseCheck] | None:
    """Return the check class for the given id, or None if not found."""
    return _CHECK_MAP.get(check_id)


def list_checks() -> list[dict[str, str]]:
    """Return a list of check metadata dicts for display."""
    return [{"id": cls.id, "title": cls.title} for cls in ALL_CHECKS]
