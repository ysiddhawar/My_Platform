from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.trade_rating import TradeRating


class RatingRepositoryError(Exception):
    pass


class RatingRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "rating_store.db"):
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
                CREATE TABLE IF NOT EXISTS trade_ratings (
                    rating_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    rating_value REAL NOT NULL,
                    scale_name TEXT NOT NULL,
                    rating_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rating_account ON trade_ratings (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rating_trade ON trade_ratings (trade_id)")
            self._connection.commit()

    def save(self, rating: TradeRating):
        if not isinstance(rating, TradeRating):
            raise RatingRepositoryError("Invalid TradeRating object")
        payload = rating.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO trade_ratings (
                    rating_id, account_id, trade_id, rating_value, scale_name,
                    rating_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["rating_id"],
                    payload["account_id"],
                    payload["trade_id"],
                    payload["rating_value"],
                    payload["scale_name"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def get_for_trade(self, trade_id: str) -> Optional[TradeRating]:
        with self._lock:
            row = self._connection.execute(
                "SELECT rating_json FROM trade_ratings WHERE trade_id = ? ORDER BY created_at DESC LIMIT 1",
                (trade_id,),
            ).fetchone()
        return TradeRating.from_dict(json.loads(row[0])) if row else None

    def get_by_account(self, account_id: str) -> List[TradeRating]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT rating_json FROM trade_ratings WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
        return [TradeRating.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM trade_ratings WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            self._connection.commit()
        return deleted

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
