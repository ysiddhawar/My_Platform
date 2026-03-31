from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Optional

from models.user_session import UserSession


class SessionRepositoryError(Exception):
    pass


class SessionRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "session_store.db"):
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
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    is_active INTEGER NOT NULL,
                    session_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (session_token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)")
            self._connection.commit()

    def save(self, session: UserSession):
        if not isinstance(session, UserSession):
            raise SessionRepositoryError("Invalid UserSession object")
        payload = session.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    session_id, user_id, session_token, is_active, session_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["session_id"],
                    payload["user_id"],
                    payload["session_token"],
                    int(payload["is_active"]),
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def get_by_token(self, session_token: str) -> Optional[UserSession]:
        with self._lock:
            row = self._connection.execute(
                "SELECT session_json FROM sessions WHERE session_token = ?",
                (session_token,),
            ).fetchone()
        return UserSession.from_dict(json.loads(row[0])) if row else None

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
