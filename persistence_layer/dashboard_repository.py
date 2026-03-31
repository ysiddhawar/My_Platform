from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.dashboard_layout import DashboardLayout


class DashboardRepositoryError(Exception):
    pass


class DashboardRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "dashboard_store.db"):
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
                CREATE TABLE IF NOT EXISTS dashboard_layouts (
                    layout_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    dashboard_name TEXT NOT NULL,
                    template_name TEXT,
                    layout_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_account ON dashboard_layouts (account_id)")
            self._connection.commit()

    def save(self, layout: DashboardLayout):
        if not isinstance(layout, DashboardLayout):
            raise DashboardRepositoryError("Invalid DashboardLayout object")
        payload = layout.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO dashboard_layouts (
                    layout_id, account_id, dashboard_name, template_name,
                    layout_json, schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["layout_id"],
                    payload["account_id"],
                    payload["dashboard_name"],
                    payload.get("template_name"),
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
            self._connection.commit()

    def get(self, layout_id: str) -> Optional[DashboardLayout]:
        with self._lock:
            row = self._connection.execute(
                "SELECT layout_json FROM dashboard_layouts WHERE layout_id = ?",
                (layout_id,),
            ).fetchone()
        return DashboardLayout.from_dict(json.loads(row[0])) if row else None

    def get_by_account(self, account_id: str) -> List[DashboardLayout]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT layout_json FROM dashboard_layouts WHERE account_id = ? ORDER BY updated_at DESC",
                (account_id,),
            ).fetchall()
        return [DashboardLayout.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
