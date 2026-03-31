from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.trade_tag import TradeTag


class TagRepositoryError(Exception):
    pass


class TagRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "tag_store.db"):
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
                CREATE TABLE IF NOT EXISTS tags (
                    tag_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tag_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_tag_links (
                    trade_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    linked_at TEXT NOT NULL,
                    PRIMARY KEY (trade_id, tag_id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_account ON tags (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_tag_trade ON trade_tag_links (trade_id)")
            self._connection.commit()

    def save(self, tag: TradeTag):
        if not isinstance(tag, TradeTag):
            raise TagRepositoryError("Invalid TradeTag object")
        payload = tag.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO tags (
                    tag_id, account_id, name, category, tag_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["tag_id"],
                    payload["account_id"],
                    payload["name"],
                    payload["category"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def assign_to_trade(self, account_id: str, trade_id: str, tag_id: str, linked_at: str):
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO trade_tag_links (trade_id, tag_id, account_id, linked_at)
                VALUES (?, ?, ?, ?)
                """,
                (trade_id, tag_id, account_id, linked_at),
            )
            self._connection.commit()

    def list_by_account(self, account_id: str) -> List[TradeTag]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT tag_json FROM tags WHERE account_id = ? ORDER BY category ASC, name ASC",
                (account_id,),
            ).fetchall()
        return [TradeTag.from_dict(json.loads(row[0])) for row in rows]

    def list_by_category(self, account_id: str, category: str) -> List[TradeTag]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT tag_json FROM tags
                WHERE account_id = ? AND category = ?
                ORDER BY name ASC
                """,
                (account_id, category),
            ).fetchall()
        return [TradeTag.from_dict(json.loads(row[0])) for row in rows]

    def get(self, tag_id: str) -> Optional[TradeTag]:
        with self._lock:
            row = self._connection.execute(
                "SELECT tag_json FROM tags WHERE tag_id = ?",
                (tag_id,),
            ).fetchone()
        return TradeTag.from_dict(json.loads(row[0])) if row else None

    def list_for_trade(self, trade_id: str) -> List[TradeTag]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT t.tag_json
                FROM tags t
                JOIN trade_tag_links l ON t.tag_id = l.tag_id
                WHERE l.trade_id = ?
                ORDER BY t.category ASC, t.name ASC
                """,
                (trade_id,),
            ).fetchall()
        return [TradeTag.from_dict(json.loads(row[0])) for row in rows]

    def delete(self, tag_id: str) -> bool:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM trade_tag_links WHERE tag_id = ?", (tag_id,))
            deleted = cursor.execute("DELETE FROM tags WHERE tag_id = ?", (tag_id,))
            self._connection.commit()
        return deleted.rowcount > 0

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM trade_tag_links WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM tags WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            self._connection.commit()
        return deleted

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
