from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.share_export_record import ShareExportRecord


class ExportRepositoryError(Exception):
    pass


class ExportRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "export_store.db"):
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
                CREATE TABLE IF NOT EXISTS share_exports (
                    record_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    record_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    format TEXT NOT NULL,
                    status TEXT NOT NULL,
                    export_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_account ON share_exports (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_target ON share_exports (target_type, target_id)")
            self._connection.commit()

    def save(self, record: ShareExportRecord):
        if not isinstance(record, ShareExportRecord):
            raise ExportRepositoryError("Invalid ShareExportRecord object")
        payload = record.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO share_exports (
                    record_id, account_id, record_type, target_type, target_id,
                    format, status, export_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["record_id"],
                    payload["account_id"],
                    payload["record_type"],
                    payload["target_type"],
                    payload["target_id"],
                    payload["format"],
                    payload["status"],
                    json.dumps(payload, default=str),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def get(self, record_id: str) -> Optional[ShareExportRecord]:
        with self._lock:
            row = self._connection.execute(
                "SELECT export_json FROM share_exports WHERE record_id = ?",
                (record_id,),
            ).fetchone()
        return ShareExportRecord.from_dict(json.loads(row[0])) if row else None

    def get_by_account(self, account_id: str) -> List[ShareExportRecord]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT export_json FROM share_exports WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
        return [ShareExportRecord.from_dict(json.loads(row[0])) for row in rows]

    def get_by_share_token(self, share_token: str) -> Optional[ShareExportRecord]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT export_json FROM share_exports ORDER BY created_at DESC"
            ).fetchall()
        for row in rows:
            record = ShareExportRecord.from_dict(json.loads(row[0]))
            if record.share_token == share_token:
                return record
        return None

    def get_by_record_type(self, account_id: str, record_type: str) -> List[ShareExportRecord]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT export_json FROM share_exports
                WHERE account_id = ? AND record_type = ?
                ORDER BY created_at DESC
                """,
                (account_id, record_type),
            ).fetchall()
        return [ShareExportRecord.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
