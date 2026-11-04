"""Unit tests for the FastAPI service."""

from __future__ import annotations

import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from sitesentry.api.app import create_app
from sitesentry.config import ApiConfig
from sitesentry.models import ScanResult, ScanStatus
from sitesentry.storage import ScanStorage


@pytest.fixture
async def app_client(tmp_path: object):  # type: ignore[no-untyped-def]
    import os

    db_path = os.path.join(str(tmp_path), "test_api.db")  # type: ignore[arg-type]
    config = ApiConfig(db_path=db_path, max_concurrent_scans=2)
    app = create_app(api_config=config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.app = app
        # Trigger lifespan
        async with app.router.lifespan_context(app):
            yield client


@pytest.fixture
async def authed_app_client(tmp_path: object):  # type: ignore[no-untyped-def]
    import os

    db_path = os.path.join(str(tmp_path), "test_api_auth.db")  # type: ignore[arg-type]
    config = ApiConfig(db_path=db_path, api_key="test-secret-key")
    app = create_app(api_config=config)
    transport = ASGITransport(app=app)
    async with (
        AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer test-secret-key"},
        ) as client,
        app.router.lifespan_context(app),
    ):
        yield client


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health(self, app_client: AsyncClient) -> None:
        resp = await app_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_ready(self, app_client: AsyncClient) -> None:
        resp = await app_client.get("/ready")
        assert resp.status_code == 200


class TestScanEndpoints:
    @pytest.mark.asyncio
    async def test_create_scan_requires_permission(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/scans",
            json={"url": "https://example.com", "confirm_permission": False},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "permission" in data.get("title", "").lower() or "permission" in str(data).lower()

    @pytest.mark.asyncio
    async def test_create_scan_invalid_url(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/scans",
            json={"url": "not-a-url", "confirm_permission": True},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_scan_accepted(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/scans",
            json={"url": "https://example.com", "confirm_permission": True},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self, app_client: AsyncClient) -> None:
        resp = await app_client.get("/api/v1/scans/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_report_formats(self, app_client: AsyncClient) -> None:
        # Save a completed scan directly
        storage: ScanStorage = app_client.app.state.storage  # type: ignore[attr-defined]
        result = ScanResult(
            scan_id="report-test-001",
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
            grade="A",
            score=100,
        )
        await storage.save_scan(result)

        for fmt in ["json", "md", "html", "sarif"]:
            resp = await app_client.get(f"/api/v1/scans/report-test-001/report?format={fmt}")
            assert resp.status_code == 200, f"Format {fmt} failed: {resp.text}"

    @pytest.mark.asyncio
    async def test_get_report_invalid_format(self, app_client: AsyncClient) -> None:
        storage: ScanStorage = app_client.app.state.storage  # type: ignore[attr-defined]
        result = ScanResult(
            scan_id="report-test-002",
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
        )
        await storage.save_scan(result)
        resp = await app_client.get("/api/v1/scans/report-test-002/report?format=xml")
        assert resp.status_code == 400


class TestApiAuth:
    @pytest.mark.asyncio
    async def test_valid_api_key(self, authed_app_client: AsyncClient) -> None:
        resp = await authed_app_client.post(
            "/api/v1/scans",
            json={"url": "https://example.com", "confirm_permission": True},
        )
        assert resp.status_code == 202

    @pytest.mark.asyncio
    async def test_missing_api_key_rejected(self, tmp_path: object) -> None:
        import os

        db_path = os.path.join(str(tmp_path), "test_noauth.db")  # type: ignore[arg-type]
        config = ApiConfig(db_path=db_path, api_key="test-secret-key")
        app = create_app(api_config=config)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with app.router.lifespan_context(app):
                resp = await client.post(
                    "/api/v1/scans",
                    json={"url": "https://example.com", "confirm_permission": True},
                )
                assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_api_key_rejected(self, tmp_path: object) -> None:
        import os

        db_path = os.path.join(str(tmp_path), "test_wrongauth.db")  # type: ignore[arg-type]
        config = ApiConfig(db_path=db_path, api_key="correct-key")
        app = create_app(api_config=config)
        transport = ASGITransport(app=app)
        async with (
            AsyncClient(
                transport=transport,
                base_url="http://test",
                headers={"Authorization": "Bearer wrong-key"},
            ) as client,
            app.router.lifespan_context(app),
        ):
            resp = await client.post(
                "/api/v1/scans",
                json={"url": "https://example.com", "confirm_permission": True},
            )
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_health_no_auth_required(self, tmp_path: object) -> None:
        """Health endpoint must be public even when API key is configured."""
        import os

        db_path = os.path.join(str(tmp_path), "test_health_auth.db")  # type: ignore[arg-type]
        config = ApiConfig(db_path=db_path, api_key="secret")
        app = create_app(api_config=config)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with app.router.lifespan_context(app):
                resp = await client.get("/health")
                assert resp.status_code == 200


class TestRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, tmp_path: object) -> None:
        import os

        db_path = os.path.join(str(tmp_path), "test_ratelimit.db")  # type: ignore[arg-type]
        config = ApiConfig(db_path=db_path, per_client_rpm=3)
        app = create_app(api_config=config)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with app.router.lifespan_context(app):
                # First 3 should succeed (or fail for other reasons, not 429)
                statuses = []
                for _ in range(5):
                    resp = await client.post(
                        "/api/v1/scans",
                        json={"url": "https://example.com", "confirm_permission": True},
                    )
                    statuses.append(resp.status_code)
                # At least one 429 should appear
                assert 429 in statuses



class TestDashboard:
    @pytest.mark.asyncio
    async def test_dashboard_is_served(self, app_client: AsyncClient) -> None:
        response = await app_client.get("/")
        assert response.status_code == 200
        assert "SiteSentry" in response.text
        assert "Start a security scan" in response.text

    @pytest.mark.asyncio
    async def test_scan_history_endpoint(self, app_client: AsyncClient) -> None:
        storage: ScanStorage = app_client.app.state.storage  # type: ignore[attr-defined]
        result = ScanResult(
            scan_id="history-test-001",
            target_url="https://example.com",
            started_at=datetime.datetime.now(datetime.UTC),
            status=ScanStatus.completed,
            grade="A",
            score=100,
        )
        await storage.save_scan(result)

        response = await app_client.get("/api/v1/scans?limit=10")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["scan_id"] == "history-test-001"
        assert items[0]["grade"] == "A"
        assert items[0]["score"] == 100

    @pytest.mark.asyncio
    async def test_scan_history_requires_api_key_when_configured(self, tmp_path: object) -> None:
        import os

        db_path = os.path.join(str(tmp_path), "history_auth.db")  # type: ignore[arg-type]
        config = ApiConfig(db_path=db_path, api_key="test-secret-key")
        app = create_app(api_config=config)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with app.router.lifespan_context(app):
                response = await client.get("/api/v1/scans")
                assert response.status_code == 401
