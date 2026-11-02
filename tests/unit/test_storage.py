"""Unit tests for SQLite storage."""

from __future__ import annotations

import datetime
import os

import pytest

from sitesentry.models import ScanResult, ScanStatus
from sitesentry.storage import ScanStorage


def make_result(scan_id: str = "test-001") -> ScanResult:
    return ScanResult(
        scan_id=scan_id,
        target_url="https://example.com",
        started_at=datetime.datetime.now(datetime.UTC),
        completed_at=datetime.datetime.now(datetime.UTC),
        status=ScanStatus.completed,
        grade="B",
        score=82,
    )


class TestScanStorage:
    @pytest.fixture
    async def storage(self, tmp_path: object) -> ScanStorage:
        db_path = os.path.join(str(tmp_path), "test.db")  # type: ignore[arg-type]
        s = ScanStorage(db_path=db_path)
        await s.init_db()
        return s

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, storage: ScanStorage) -> None:
        result = make_result("test-001")
        await storage.save_scan(result)
        retrieved = await storage.get_scan("test-001")
        assert retrieved is not None
        assert retrieved.target_url == "https://example.com"
        assert retrieved.grade == "B"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage: ScanStorage) -> None:
        result = await storage.get_scan("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_scans(self, storage: ScanStorage) -> None:
        for i in range(3):
            await storage.save_scan(make_result(f"scan-{i}"))
        summaries = await storage.list_scans(limit=10)
        assert len(summaries) == 3

    @pytest.mark.asyncio
    async def test_list_scans_limit(self, storage: ScanStorage) -> None:
        for i in range(5):
            await storage.save_scan(make_result(f"scan-{i}"))
        summaries = await storage.list_scans(limit=2)
        assert len(summaries) == 2

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, storage: ScanStorage) -> None:
        import aiosqlite

        async with aiosqlite.connect(storage._db_path) as db:
            async with db.execute("PRAGMA journal_mode;") as cur:
                row = await cur.fetchone()
        assert row is not None
        assert row[0].lower() == "wal"

    @pytest.mark.asyncio
    async def test_update_status(self, storage: ScanStorage) -> None:
        result = make_result("scan-status-test")
        result.status = ScanStatus.pending
        await storage.save_scan(result)
        await storage.update_scan_status("scan-status-test", ScanStatus.running)
        updated = await storage.get_scan("scan-status-test")
        assert updated is not None
        assert updated.status == ScanStatus.running
