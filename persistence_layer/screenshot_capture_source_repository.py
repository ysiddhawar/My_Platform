from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.screenshot_capture_source import ScreenshotCaptureSource


class ScreenshotCaptureSourceRepositoryError(Exception):
    pass


class ScreenshotCaptureSourceRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "screenshot_capture_source_store.db"):
        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL;")
        self._connection.execute("PRAGMA synchronous=FULL;")
        self._create_schema()

    def _create_schema(self):
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS screenshot_capture_sources (
                    source_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_capture_source_type ON screenshot_capture_sources (source_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_capture_source_status ON screenshot_capture_sources (status)")
            self._connection.commit()

    def save(self, source: ScreenshotCaptureSource):
        if not isinstance(source, ScreenshotCaptureSource):
            raise ScreenshotCaptureSourceRepositoryError("Invalid ScreenshotCaptureSource object")
        payload = source.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO screenshot_capture_sources (
                    source_id, source_type, status, source_json, schema_version, created_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["source_id"],
                    payload["source_type"],
                    payload["status"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                    payload["last_seen_at"],
                ),
            )
            self._connection.commit()

    def get(self, source_id: str) -> Optional[ScreenshotCaptureSource]:
        with self._lock:
            row = self._connection.execute(
                "SELECT source_json FROM screenshot_capture_sources WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return ScreenshotCaptureSource.from_dict(json.loads(row[0])) if row else None

    def list_all(self, status: Optional[str] = None) -> List[ScreenshotCaptureSource]:
        query = "SELECT source_json FROM screenshot_capture_sources"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY last_seen_at DESC"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [ScreenshotCaptureSource.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
