"""Scan aggregator – orchestrates crawl → checks → score → result."""

from __future__ import annotations

import asyncio
import datetime
import logging
import uuid
from typing import Any

import httpx

from sitesentry import __repo__, __version__
from sitesentry.checks.base import ScanContext
from sitesentry.checks.registry import ALL_CHECKS
from sitesentry.config import ScanConfig
from sitesentry.crawler import Crawler, PermissionDeniedError
from sitesentry.models import CheckResult, Finding, PageData, ScanResult, ScanStatus
from sitesentry.scope import ScopeGuard
from sitesentry.scoring import compute_score

logger = logging.getLogger(__name__)

USER_AGENT = f"SiteSentry/{__version__} (+{__repo__})"


async def _run_check_safe(
    check_cls: Any,
    context: ScanContext,
) -> CheckResult:
    """Run a single check, catching all exceptions for crash isolation."""
    check = check_cls()
    result = CheckResult(check_id=check.id, title=check.title)
    try:
        result.findings = await check.run(context)
    except Exception as exc:
        logger.exception("Check %s failed: %s", check.id, exc)
        result.error = str(exc)
        result.incomplete = True
    return result


class ScanAggregator:
    """Orchestrates a complete scan from start to ScanResult."""

    def __init__(self, config: ScanConfig) -> None:
        self._config = config

    async def run_scan(self) -> ScanResult:
        """Run the full scan pipeline and return a ScanResult."""
        scan_id = str(uuid.uuid4())
        started_at = datetime.datetime.now(datetime.UTC)

        result = ScanResult(
            scan_id=scan_id,
            target_url=self._config.target_url,
            started_at=started_at,
            status=ScanStatus.running,
        )

        try:
            result = await asyncio.wait_for(
                self._do_scan(result),
                timeout=self._config.scan_timeout,
            )
        except TimeoutError:
            logger.warning("Scan timed out after %ss", self._config.scan_timeout)
            result.status = ScanStatus.failed
            result.errors.append(f"Scan timed out after {self._config.scan_timeout}s")
            result.completed_at = datetime.datetime.now(datetime.UTC)
        except PermissionDeniedError as exc:
            result.status = ScanStatus.failed
            result.errors.append(str(exc))
            result.completed_at = datetime.datetime.now(datetime.UTC)
        except Exception as exc:
            logger.exception("Scan failed: %s", exc)
            result.status = ScanStatus.failed
            result.errors.append(str(exc))
            result.completed_at = datetime.datetime.now(datetime.UTC)

        return result

    async def _do_scan(self, result: ScanResult) -> ScanResult:
        """Inner scan pipeline (wrapped by timeout in run_scan)."""
        config = self._config
        scope = ScopeGuard(config.target_url, allow_private=config.allow_private)

        # ── 1. Crawl ──────────────────────────────────────────────────
        pages: list[PageData] = []
        async with Crawler(config, scope) as crawler:
            async for page in crawler.crawl():
                pages.append(page)
            soft_404 = crawler.soft_404_page

        result.page_count = len(pages)
        result.pages_scanned = [p.url for p in pages]
        logger.info("Crawled %d pages", len(pages))

        # ── 2. Build check context ─────────────────────────────────────
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=httpx.Timeout(config.request_timeout),
            follow_redirects=True,
        ) as http_client:
            context = ScanContext(
                target_url=config.target_url,
                pages=pages,
                soft_404=soft_404,
                config=config,
                http_client=http_client,
            )

            # ── 3. Run all checks concurrently (crash-isolated) ────────
            check_tasks = [_run_check_safe(check_cls, context) for check_cls in ALL_CHECKS]
            check_results: list[CheckResult] = await asyncio.gather(*check_tasks)

        # ── 4. De-duplicate findings across pages ─────────────────────
        for cr in check_results:
            cr.findings = _deduplicate_findings(cr.findings)

        has_incomplete = any(cr.incomplete for cr in check_results)

        # ── 5. Score ───────────────────────────────────────────────────
        score, grade, breakdown = compute_score(check_results, has_incomplete=has_incomplete)

        # ── 6. Build final result ──────────────────────────────────────
        result.results = list(check_results)
        result.score = score
        result.grade = grade
        result.breakdown = breakdown
        result.has_incomplete_checks = has_incomplete
        result.completed_at = datetime.datetime.now(datetime.UTC)
        result.status = ScanStatus.completed

        return result


def _deduplicate_findings(
    findings: list[Finding],
) -> list[Finding]:
    """Remove duplicate findings by dedupe_key, preserving order."""
    seen: set[str] = set()
    unique: list[Finding] = []
    for f in findings:
        if f.dedupe_key not in seen:
            seen.add(f.dedupe_key)
            unique.append(f)
    return unique
