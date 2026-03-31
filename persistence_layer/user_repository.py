from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.auth_user import AuthUser


class UserRepositoryError(Exception):
    pass


class UserRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "user_store.db"):
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
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    user_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            self._connection.commit()

    def save(self, user: AuthUser):
        if not isinstance(user, AuthUser):
            raise UserRepositoryError("Invalid AuthUser object")
        payload = user.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO users (
                    user_id, username, user_json, schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["user_id"],
                    payload["username"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
            self._connection.commit()

    def get_by_username(self, username: str) -> Optional[AuthUser]:
        with self._lock:
            row = self._connection.execute(
                "SELECT user_json FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return AuthUser.from_dict(json.loads(row[0])) if row else None

    def get(self, user_id: str) -> Optional[AuthUser]:
        with self._lock:
            row = self._connection.execute(
                "SELECT user_json FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return AuthUser.from_dict(json.loads(row[0])) if row else None

    def list_users(self) -> List[AuthUser]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT user_json FROM users ORDER BY created_at ASC"
            ).fetchall()
        return [AuthUser.from_dict(json.loads(row[0])) for row in rows]

    def count(self) -> int:
        with self._lock:
            row = self._connection.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0] if row else 0)

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
