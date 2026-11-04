"""FastAPI route handlers."""

from __future__ import annotations

import asyncio
import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, field_validator

from sitesentry.api.auth import verify_api_key
from sitesentry.api.ratelimit import RateLimiter
from sitesentry.config import ScanConfig
from sitesentry.dashboard import DASHBOARD_HTML
from sitesentry.models import OutputFormat, ScanResult, ScanStatus
from sitesentry.report import ReportGenerator
from sitesentry.storage import ScanStorage

router = APIRouter()
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60.0, max_clients=1000)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ScanRequest(BaseModel):
    url: str
    confirm_permission: bool = False
    max_pages: int = 50
    max_depth: int = 2
    ignore_robots: bool = False
    allow_private: bool = False

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v


def _problem(status_code: int, title: str, detail: str) -> dict[str, Any]:
    return {
        "type": f"https://sitesentry.invalid/errors/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status_code,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Dependency: get storage from app state
# ---------------------------------------------------------------------------


def get_storage(request: Request) -> ScanStorage:
    return request.app.state.storage  # type: ignore[no-any-return]


def get_api_config(request: Request) -> Any:
    return request.app.state.api_config


def get_worker_semaphore(request: Request) -> asyncio.Semaphore:
    return request.app.state.worker_semaphore  # type: ignore[no-any-return]


def get_rate_limiter(request: Request) -> RateLimiter:
    val = getattr(request.app.state, "rate_limiter", _rate_limiter)
    if not isinstance(val, RateLimiter):
        return _rate_limiter
    return val


# ---------------------------------------------------------------------------
# Health / Ready
# ---------------------------------------------------------------------------


@router.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["meta"])
async def ready(storage: ScanStorage = Depends(get_storage)) -> dict[str, str]:
    try:
        # Verify DB is accessible
        await storage.list_scans(limit=1)
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_problem(503, "Service Unavailable", str(exc)),
        )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    """Serve the self-contained web dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/api/v1/scans", tags=["scans"])
async def list_scans(
    request: Request,
    limit: int = 30,
    storage: ScanStorage = Depends(get_storage),
    api_config: Any = Depends(get_api_config),
) -> list[dict[str, Any]]:
    """Return recent scan summaries for the dashboard."""
    verify_api_key(api_config.api_key, request)
    bounded_limit = max(1, min(limit, 100))
    summaries = await storage.list_scans(limit=bounded_limit)
    return [summary.model_dump(mode="json") for summary in summaries]


# ---------------------------------------------------------------------------
# POST /api/v1/scans
# ---------------------------------------------------------------------------


@router.post("/api/v1/scans", status_code=status.HTTP_202_ACCEPTED, tags=["scans"])
async def create_scan(
    body: ScanRequest,
    request: Request,
    storage: ScanStorage = Depends(get_storage),
    api_config: Any = Depends(get_api_config),
    semaphore: asyncio.Semaphore = Depends(get_worker_semaphore),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict[str, Any]:
    # Auth
    verify_api_key(api_config.api_key, request)

    # Rate limit by client IP
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_problem(
                429,
                "Too Many Requests",
                f"Rate limit exceeded. Maximum {api_config.per_client_rpm} requests per minute.",
            ),
        )

    # Permission gate
    if not body.confirm_permission:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_problem(
                422,
                "Permission Required",
                "confirm_permission must be true. Only scan sites you own or "
                "are authorised to test.",
            ),
        )

    # Create a pending scan record
    scan_id = str(uuid.uuid4())
    placeholder = ScanResult(
        scan_id=scan_id,
        target_url=body.url,
        started_at=datetime.datetime.now(datetime.UTC),
        status=ScanStatus.pending,
    )
    await storage.save_scan(placeholder)

    # Launch background task
    config = ScanConfig(
        target_url=body.url,
        confirm_permission=True,
        max_pages=body.max_pages,
        max_depth=body.max_depth,
        ignore_robots=body.ignore_robots,
        allow_private=body.allow_private,
    )
    task = asyncio.create_task(
        _run_scan_background(scan_id, config, storage, semaphore),
        name=f"sitesentry-scan-{scan_id}",
    )
    scan_tasks: set[asyncio.Task[None]] = request.app.state.scan_tasks
    scan_tasks.add(task)
    task.add_done_callback(scan_tasks.discard)

    return {"id": scan_id, "status": "pending"}


async def _run_scan_background(
    scan_id: str,
    config: ScanConfig,
    storage: ScanStorage,
    semaphore: asyncio.Semaphore,
) -> None:
    """Run a scan as a background task, bounded by the worker semaphore."""
    from sitesentry.aggregator import ScanAggregator

    async with semaphore:
        await storage.update_scan_status(scan_id, ScanStatus.running)
        try:
            result = await ScanAggregator(config).run_scan()
            result.scan_id = scan_id
            await storage.save_scan(result)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Background scan %s failed", scan_id)
            await storage.update_scan_status(scan_id, ScanStatus.failed)


# ---------------------------------------------------------------------------
# GET /api/v1/scans/{id}
# ---------------------------------------------------------------------------


@router.get("/api/v1/scans/{scan_id}", tags=["scans"])
async def get_scan(
    scan_id: str,
    request: Request,
    storage: ScanStorage = Depends(get_storage),
    api_config: Any = Depends(get_api_config),
) -> dict[str, Any]:
    verify_api_key(api_config.api_key, request)
    result = await storage.get_scan(scan_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_problem(404, "Not Found", f"Scan {scan_id!r} not found."),
        )
    return result.model_dump(mode="json")


# ---------------------------------------------------------------------------
# GET /api/v1/scans/{id}/report
# ---------------------------------------------------------------------------


@router.get("/api/v1/scans/{scan_id}/report", tags=["scans"])
async def get_report(
    scan_id: str,
    format: str = "json",
    request: Request = ...,  # type: ignore[assignment]
    storage: ScanStorage = Depends(get_storage),
    api_config: Any = Depends(get_api_config),
) -> Any:
    verify_api_key(api_config.api_key, request)
    result = await storage.get_scan(scan_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_problem(404, "Not Found", f"Scan {scan_id!r} not found."),
        )

    gen = ReportGenerator()
    try:
        fmt = OutputFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_problem(400, "Bad Request", f"Unknown format {format!r}."),
        )

    if fmt == OutputFormat.json:
        return JSONResponse(content=result.model_dump(mode="json"))
    elif fmt == OutputFormat.markdown:
        return PlainTextResponse(gen.to_markdown(result), media_type="text/markdown")
    elif fmt == OutputFormat.html:
        return HTMLResponse(gen.to_html(result))
    elif fmt == OutputFormat.sarif:
        return PlainTextResponse(gen.to_sarif(result), media_type="application/sarif+json")

    return JSONResponse(content=result.model_dump(mode="json"))
