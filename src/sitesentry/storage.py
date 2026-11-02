"""SQLite scan history with WAL mode via aiosqlite."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from sitesentry.models import ScanResult, ScanStatus, ScanSummary

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    target_url TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    grade TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    finding_count INTEGER NOT NULL DEFAULT 0,
    result_json TEXT NOT NULL
);
"""

_ENABLE_WAL = "PRAGMA journal_mode=WAL;"


class ScanStorage:
    """Async SQLite storage for scan results."""

    def __init__(self, db_path: str = "sitesentry.db") -> None:
        self._db_path = db_path

    async def init_db(self) -> None:
        """Create tables and enable WAL mode."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_ENABLE_WAL)
            await db.execute(_CREATE_TABLE)
            await db.commit()
        logger.debug("Database initialised at %s", self._db_path)

    async def save_scan(self, result: ScanResult) -> str:
        """Persist a ScanResult. Returns the scan_id."""
        if not result.scan_id:
            result.scan_id = str(uuid.uuid4())

        finding_count = len(result.all_findings)
        result_json = result.model_dump_json()

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_ENABLE_WAL)
            await db.execute(
                """
                INSERT OR REPLACE INTO scans
                    (id, target_url, started_at, completed_at, status,
                     grade, score, finding_count, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.scan_id,
                    result.target_url,
                    result.started_at.isoformat(),
                    result.completed_at.isoformat() if result.completed_at else None,
                    result.status.value,
                    result.grade,
                    result.score,
                    finding_count,
                    result_json,
                ),
            )
            await db.commit()

        logger.debug("Saved scan %s", result.scan_id)
        return result.scan_id

    async def get_scan(self, scan_id: str) -> ScanResult | None:
        """Retrieve a scan by ID. Returns None if not found."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_ENABLE_WAL)
            async with db.execute(
                "SELECT status, result_json FROM scans WHERE id = ?", (scan_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            return None

        scan = ScanResult.model_validate_json(row[1])
        scan.status = ScanStatus(row[0])
        return scan

    async def update_scan_status(self, scan_id: str, status: ScanStatus) -> None:
        """Update just the status column (used for pending→running transitions)."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_ENABLE_WAL)
            async with db.execute("SELECT result_json FROM scans WHERE id = ?", (scan_id,)) as cur:
                row = await cur.fetchone()
            if row:
                res = ScanResult.model_validate_json(row[0])
                res.status = status
                await db.execute(
                    "UPDATE scans SET status = ?, result_json = ? WHERE id = ?",
                    (status.value, res.model_dump_json(), scan_id),
                )
            else:
                await db.execute(
                    "UPDATE scans SET status = ? WHERE id = ?",
                    (status.value, scan_id),
                )
            await db.commit()

    async def list_scans(self, limit: int = 20) -> list[ScanSummary]:
        """Return lightweight summaries for the most recent scans."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_ENABLE_WAL)
            async with db.execute(
                """
                SELECT id, target_url, started_at, completed_at, status,
                       grade, score, finding_count
                FROM scans
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            ScanSummary(
                scan_id=row[0],
                target_url=row[1],
                started_at=datetime.fromisoformat(row[2]).replace(tzinfo=UTC),
                completed_at=(
                    datetime.fromisoformat(row[3]).replace(tzinfo=UTC) if row[3] else None
                ),
                status=ScanStatus(row[4]),
                grade=row[5],
                score=row[6],
                finding_count=row[7],
            )
            for row in rows
        ]
