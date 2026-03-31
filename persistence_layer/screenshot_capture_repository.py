from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.screenshot_capture_request import ScreenshotCaptureRequest


class ScreenshotCaptureRepositoryError(Exception):
    pass


class ScreenshotCaptureRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "screenshot_capture_store.db"):
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
                CREATE TABLE IF NOT EXISTS screenshot_capture_requests (
                    request_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    requested_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_capture_account ON screenshot_capture_requests (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_capture_trade ON screenshot_capture_requests (trade_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_capture_status ON screenshot_capture_requests (status)")
            self._connection.commit()

    def save(self, request: ScreenshotCaptureRequest):
        if not isinstance(request, ScreenshotCaptureRequest):
            raise ScreenshotCaptureRepositoryError("Invalid ScreenshotCaptureRequest object")
        payload = request.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO screenshot_capture_requests (
                    request_id, account_id, trade_id, status, request_json, schema_version, requested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["request_id"],
                    payload["account_id"],
                    payload["trade_id"],
                    payload["status"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["requested_at"],
                ),
            )
            self._connection.commit()

    def get(self, request_id: str) -> Optional[ScreenshotCaptureRequest]:
        with self._lock:
            row = self._connection.execute(
                "SELECT request_json FROM screenshot_capture_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return ScreenshotCaptureRequest.from_dict(json.loads(row[0])) if row else None

    def get_by_trade(self, trade_id: str) -> List[ScreenshotCaptureRequest]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT request_json FROM screenshot_capture_requests WHERE trade_id = ? ORDER BY requested_at DESC",
                (trade_id,),
            ).fetchall()
        return [ScreenshotCaptureRequest.from_dict(json.loads(row[0])) for row in rows]

    def get_by_status(self, status: str) -> List[ScreenshotCaptureRequest]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT request_json FROM screenshot_capture_requests WHERE status = ? ORDER BY requested_at ASC",
                (status,),
            ).fetchall()
        return [ScreenshotCaptureRequest.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
