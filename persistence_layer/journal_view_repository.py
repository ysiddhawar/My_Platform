from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.journal_view import JournalViewConfig


class JournalViewRepositoryError(Exception):
    pass


class JournalViewRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "journal_view_store.db"):
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
                CREATE TABLE IF NOT EXISTS journal_views (
                    view_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    view_name TEXT,
                    view_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_view_account ON journal_views (account_id)")
            self._connection.commit()

    def save(self, view: JournalViewConfig, view_name: Optional[str] = None):
        if not isinstance(view, JournalViewConfig):
            raise JournalViewRepositoryError("Invalid JournalViewConfig object")
        payload = view.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO journal_views (
                    view_id, account_id, view_name, view_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["view_id"],
                    payload["account_id"],
                    view_name or payload["metadata"].get("name"),
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def get(self, view_id: str) -> Optional[JournalViewConfig]:
        with self._lock:
            row = self._connection.execute(
                "SELECT view_json FROM journal_views WHERE view_id = ?",
                (view_id,),
            ).fetchone()
        return JournalViewConfig.from_dict(json.loads(row[0])) if row else None

    def get_by_account(self, account_id: str) -> List[JournalViewConfig]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT view_json FROM journal_views WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
        return [JournalViewConfig.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
