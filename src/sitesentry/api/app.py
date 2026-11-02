"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from sitesentry import __version__
from sitesentry.api.ratelimit import RateLimiter
from sitesentry.api.routes import router
from sitesentry.config import ApiConfig
from sitesentry.storage import ScanStorage


def create_app(api_config: ApiConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if api_config is None:
        api_config = ApiConfig()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Startup
        storage = ScanStorage(db_path=api_config.db_path)
        await storage.init_db()
        app.state.storage = storage
        app.state.api_config = api_config
        app.state.worker_semaphore = asyncio.Semaphore(api_config.max_concurrent_scans)
        app.state.rate_limiter = RateLimiter(
            max_requests=api_config.per_client_rpm, window_seconds=60.0, max_clients=1000
        )
        app.state.db_ready = True
        yield
        # Shutdown (nothing to clean up)
        app.state.db_ready = False

    app = FastAPI(
        title="SiteSentry",
        description="Passive, safe-by-default web security scanner API",
        version=__version__,
        lifespan=lifespan,
        # CORS is off by default – do not add CORSMiddleware here
    )

    # RFC 7807 error response handler
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "type": "https://sitesentry.invalid/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": str(exc.errors()),
            },
        )

    app.include_router(router)
    return app
