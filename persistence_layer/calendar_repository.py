from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List

from models.calendar_view import CalendarColorState, CalendarDaySummary


class CalendarRepositoryError(Exception):
    pass


class CalendarRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "calendar_store.db"):
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
                CREATE TABLE IF NOT EXISTS calendar_day_summaries (
                    account_id TEXT NOT NULL,
                    day TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    PRIMARY KEY (account_id, day)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_color_states (
                    account_id TEXT NOT NULL,
                    state_key TEXT NOT NULL,
                    color_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    PRIMARY KEY (account_id, state_key)
                )
                """
            )
            self._connection.commit()

    def save_day_summary(self, summary: CalendarDaySummary):
        payload = summary.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO calendar_day_summaries (
                    account_id, day, summary_json, schema_version
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    payload["account_id"],
                    payload["day"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                ),
            )
            self._connection.commit()

    def list_day_summaries(self, account_id: str) -> List[CalendarDaySummary]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT summary_json FROM calendar_day_summaries WHERE account_id = ? ORDER BY day ASC",
                (account_id,),
            ).fetchall()
        return [CalendarDaySummary.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM calendar_day_summaries WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            cursor.execute("DELETE FROM calendar_color_states WHERE account_id = ?", (account_id,))
            self._connection.commit()
        return deleted

    def save_color_state(self, account_id: str, state: CalendarColorState):
        payload = state.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO calendar_color_states (
                    account_id, state_key, color_json, schema_version
                ) VALUES (?, ?, ?, ?)
                """,
                (account_id, payload["key"], json.dumps(payload), self.SCHEMA_VERSION),
            )
            self._connection.commit()

    def list_color_states(self, account_id: str) -> List[CalendarColorState]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT color_json FROM calendar_color_states WHERE account_id = ? ORDER BY state_key ASC",
                (account_id,),
            ).fetchall()
        return [CalendarColorState.from_dict(json.loads(row[0])) for row in rows]

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
