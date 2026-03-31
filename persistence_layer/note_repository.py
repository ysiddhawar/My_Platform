from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.journal_note import JournalNote


class NoteRepositoryError(Exception):
    pass


class NoteRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "note_store.db"):
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
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    note_type TEXT NOT NULL,
                    trade_id TEXT,
                    note_date TEXT,
                    title TEXT NOT NULL,
                    note_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_account ON notes (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_trade ON notes (trade_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_date ON notes (note_date)")
            self._connection.commit()

    def save(self, note: JournalNote):
        if not isinstance(note, JournalNote):
            raise NoteRepositoryError("Invalid JournalNote object")
        payload = note.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO notes (
                    note_id, account_id, note_type, trade_id, note_date, title,
                    note_json, schema_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["note_id"],
                    payload["account_id"],
                    payload["note_type"],
                    payload.get("trade_id"),
                    payload.get("note_date"),
                    payload["title"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
            self._connection.commit()

    def get(self, note_id: str) -> Optional[JournalNote]:
        with self._lock:
            row = self._connection.execute(
                "SELECT note_json FROM notes WHERE note_id = ?",
                (note_id,),
            ).fetchone()
        return JournalNote.from_dict(json.loads(row[0])) if row else None

    def get_by_account(self, account_id: str, note_type: Optional[str] = None) -> List[JournalNote]:
        query = "SELECT note_json FROM notes WHERE account_id = ?"
        params = [account_id]
        if note_type:
            query += " AND note_type = ?"
            params.append(note_type)
        query += " ORDER BY updated_at DESC"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [JournalNote.from_dict(json.loads(row[0])) for row in rows]

    def get_by_trade(self, trade_id: str) -> List[JournalNote]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT note_json FROM notes WHERE trade_id = ? ORDER BY updated_at DESC",
                (trade_id,),
            ).fetchall()
        return [JournalNote.from_dict(json.loads(row[0])) for row in rows]

    def get_by_date(self, account_id: str, note_date: str) -> List[JournalNote]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT note_json FROM notes WHERE account_id = ? AND note_date = ? ORDER BY updated_at DESC",
                (account_id, note_date),
            ).fetchall()
        return [JournalNote.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM notes WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            self._connection.commit()
        return deleted

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
