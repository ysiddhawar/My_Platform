from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.trade_attachment import TradeAttachment


class AttachmentRepositoryError(Exception):
    pass


class AttachmentRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "attachment_store.db"):
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
                CREATE TABLE IF NOT EXISTS attachments (
                    attachment_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    attachment_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    attachment_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attachment_account ON attachments (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attachment_trade ON attachments (trade_id)")
            self._connection.commit()

    def save(self, attachment: TradeAttachment):
        if not isinstance(attachment, TradeAttachment):
            raise AttachmentRepositoryError("Invalid TradeAttachment object")
        payload = attachment.to_dict()
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO attachments (
                    attachment_id, account_id, trade_id, attachment_type, source,
                    attachment_json, schema_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["attachment_id"],
                    payload["account_id"],
                    payload["trade_id"],
                    payload["attachment_type"],
                    payload["source"],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                    payload["created_at"],
                ),
            )
            self._connection.commit()

    def get(self, attachment_id: str) -> Optional[TradeAttachment]:
        with self._lock:
            row = self._connection.execute(
                "SELECT attachment_json FROM attachments WHERE attachment_id = ?",
                (attachment_id,),
            ).fetchone()
        return TradeAttachment.from_dict(json.loads(row[0])) if row else None

    def get_by_trade(self, trade_id: str) -> List[TradeAttachment]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT attachment_json FROM attachments WHERE trade_id = ? ORDER BY created_at ASC",
                (trade_id,),
            ).fetchall()
        return [TradeAttachment.from_dict(json.loads(row[0])) for row in rows]

    def get_by_account(self, account_id: str) -> List[TradeAttachment]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT attachment_json FROM attachments WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
        return [TradeAttachment.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM attachments WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            self._connection.commit()
        return deleted

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
