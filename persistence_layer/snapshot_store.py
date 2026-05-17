from __future__ import annotations

from typing import Dict, Any, Optional
from threading import RLock
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path

from core.context import Context


class SnapshotStoreError(Exception):
    pass


class SnapshotStore:
    """
    Institutional Snapshot Engine

    Responsibilities:
    - Persist serialized Context state
    - Store last applied sequence_id
    - Enable fast crash recovery
    - Account-level isolation
    - Atomic snapshot replacement
    - Deterministic restoration
    """

    def __init__(self, db_path: str = "snapshot_store.db"):

        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None
        self._initialize()

    @property
    def _conn(self) -> sqlite3.Connection:
        assert self._connection is not None
        return self._connection

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def _initialize(self):

        with self._lock:

            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )

            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=FULL;")

            self._create_schema()

    def _create_schema(self):

        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                account_id TEXT PRIMARY KEY,
                sequence_id INTEGER NOT NULL,
                snapshot_data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        self._conn.commit()

    # ==========================================================
    # SAVE SNAPSHOT
    # ==========================================================

    def save_snapshot(
        self,
        account_id: str,
        context: Context,
        sequence_id: int,
    ):

        if not account_id:
            raise SnapshotStoreError("account_id required")

        if not isinstance(sequence_id, int):
            raise SnapshotStoreError("sequence_id must be int")

        with self._lock:

            serialized = self._serialize_context(context)

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO snapshots (
                        account_id,
                        sequence_id,
                        snapshot_data,
                        created_at
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    account_id,
                    sequence_id,
                    serialized,
                    datetime.now(timezone.utc).isoformat(),
                ))

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise SnapshotStoreError(str(e))

    # ==========================================================
    # LOAD SNAPSHOT
    # ==========================================================

    def load_snapshot(
        self,
        account_id: str
    ) -> Optional[Dict[str, Any]]:

        with self._lock:

            cursor = self._conn.cursor()

            cursor.execute("""
                SELECT sequence_id, snapshot_data
                FROM snapshots
                WHERE account_id = ?
            """, (account_id,))

            row = cursor.fetchone()

        if not row:
            return None

        sequence_id, snapshot_data = row

        return {
            "sequence_id": sequence_id,
            "context_state": json.loads(snapshot_data),
        }

    def load_latest_snapshot(
        self,
        account_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Backward-compatible alias expected by recovery engine.
        """
        if not account_id:
            return None

        row = self.load_snapshot(account_id)
        if not row:
            return None

        return {
            "sequence_id": row["sequence_id"],
            "state": row["context_state"],
            "schema_version": row["context_state"].get("schema_version"),
        }

    # ==========================================================
    # CONTEXT SERIALIZATION
    # ==========================================================

    def _serialize_context(self, context: Context) -> str:

        if not hasattr(context, "to_dict"):
            raise SnapshotStoreError(
                "Context must implement to_dict() for snapshotting"
            )

        state = context.to_dict()

        return json.dumps(state)

    def restore_context(
        self,
        context: Context,
        snapshot_state: Dict[str, Any],
    ):

        if not hasattr(context, "load_from_dict"):
            raise SnapshotStoreError(
                "Context must implement load_from_dict()"
            )

        context.load_from_dict(snapshot_state)

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._conn.close()
                self._connection: sqlite3.Connection | None = None
