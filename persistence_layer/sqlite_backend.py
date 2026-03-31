from __future__ import annotations

import sqlite3
import json
from typing import Dict, List, Any
from threading import RLock
from pathlib import Path

from persistence_layer.storage_backend import StorageBackend, StorageBackendError


class SQLiteBackend(StorageBackend):
    """
    Institutional SQLite Storage Backend

    Guarantees:
    - Append-only durability
    - WAL mode enabled
    - Atomic transactions
    - Indexed reads
    - Restart-safe
    - Thread-safe
    """

    def __init__(self, db_path: str = "event_store.db"):
        super().__init__()

        self._db_path = Path(db_path)
        self._connection = None
        self._initialize()

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def _initialize(self):

        with self._lock:

            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )

            self._connection.execute("PRAGMA journal_mode=WAL;")
            self._connection.execute("PRAGMA synchronous=FULL;")

            self._create_schema()

    def _create_schema(self):

        cursor = self._connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence_id INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                account_id TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type
            ON events (event_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_account_id
            ON events (account_id)
        """)

        self._connection.commit()

    # ==========================================================
    # APPEND
    # ==========================================================

    def append(self, record: Dict[str, Any]) -> None:

        if not isinstance(record, dict):
            raise StorageBackendError("Record must be dict")

        required_fields = [
            "sequence_id",
            "event_id",
            "event_type",
            "timestamp",
        ]

        for field in required_fields:
            if field not in record:
                raise StorageBackendError(f"Missing required field: {field}")

        with self._lock:

            try:
                cursor = self._connection.cursor()

                cursor.execute("""
                    INSERT INTO events (
                        sequence_id,
                        event_id,
                        event_type,
                        timestamp,
                        metadata,
                        account_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record["sequence_id"],
                    record["event_id"],
                    record["event_type"],
                    record["timestamp"],
                    json.dumps(record.get("metadata")),
                    record.get("account_id"),
                ))

                self._connection.commit()

            except sqlite3.Error as e:
                self._connection.rollback()
                raise StorageBackendError(str(e))

    # ==========================================================
    # READ ALL
    # ==========================================================

    def read_all(self) -> List[Dict[str, Any]]:

        with self._lock:

            cursor = self._connection.cursor()

            cursor.execute("""
                SELECT sequence_id, event_id, event_type,
                       timestamp, metadata, account_id
                FROM events
                ORDER BY sequence_id ASC
            """)

            rows = cursor.fetchall()

        return [self._row_to_record(row) for row in rows]

    # ==========================================================
    # OPTIONAL FILTERED READ
    # ==========================================================

    def read_filtered(
        self,
        *,
        event_type: str | None = None,
        account_id: str | None = None,
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT sequence_id, event_id, event_type,
                   timestamp, metadata, account_id
            FROM events
        """

        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if account_id:
            conditions.append("account_id = ?")
            params.append(account_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY sequence_id ASC"

        with self._lock:

            cursor = self._connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_record(row) for row in rows]

    # ==========================================================
    # UTILITIES
    # ==========================================================

    def _row_to_record(self, row):

        sequence_id, event_id, event_type, timestamp, metadata, account_id = row

        return {
            "sequence_id": sequence_id,
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "metadata": json.loads(metadata) if metadata else None,
            "account_id": account_id,
        }

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None