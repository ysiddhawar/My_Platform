from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from threading import RLock
from typing import Optional, Dict, Any, List


class ConfigRepositoryError(Exception):
    pass


class ConfigRepository:
    """
    Institutional Configuration Repository

    Responsibilities:
    - Persist versioned execution configurations
    - Maintain active config pointer
    - Enable safe hot reload
    - Support rollback
    - Enable recovery rebuild
    - Maintain full audit trail
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "config_store.db"):

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

        # Versioned configs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configs (
                config_version INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                config_json TEXT NOT NULL,
                source TEXT NOT NULL,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Active config pointer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_config (
                account_id TEXT PRIMARY KEY,
                config_version INTEGER NOT NULL,
                activated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_config_account
            ON configs (account_id)
        """)

        self._conn.commit()

    # ==========================================================
    # CREATE NEW CONFIG VERSION
    # ==========================================================

    def create_new_version(
        self,
        account_id: str,
        config: Dict[str, Any],
        source: str,
        timestamp: str,
    ) -> int:

        if not isinstance(config, dict):
            raise ConfigRepositoryError("Config must be dictionary")

        with self._lock:

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT INTO configs (
                        account_id,
                        config_json,
                        source,
                        schema_version,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    account_id,
                    json.dumps(config),
                    source,
                    self.SCHEMA_VERSION,
                    timestamp,
                ))

                version = cursor.lastrowid or 0
                self._conn.commit()
                return version

            except sqlite3.Error as e:
                self._conn.rollback()
                raise ConfigRepositoryError(str(e))

    # ==========================================================
    # ACTIVATE CONFIG VERSION
    # ==========================================================

    def activate_version(
        self,
        account_id: str,
        config_version: int,
        timestamp: str,
    ):

        with self._lock:

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO active_config (
                        account_id,
                        config_version,
                        activated_at
                    )
                    VALUES (?, ?, ?)
                """, (
                    account_id,
                    config_version,
                    timestamp,
                ))

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise ConfigRepositoryError(str(e))

    # ==========================================================
    # GET ACTIVE CONFIG
    # ==========================================================

    def get_active_config(
        self,
        account_id: str
    ) -> Optional[Dict[str, Any]]:

        with self._lock:
            cursor = self._conn.cursor()

            cursor.execute("""
                SELECT c.config_json
                FROM configs c
                JOIN active_config a
                ON c.config_version = a.config_version
                WHERE a.account_id = ?
            """, (account_id,))

            row = cursor.fetchone()

        if not row:
            return None

        return json.loads(row[0])

    # ==========================================================
    # GET CONFIG HISTORY
    # ==========================================================

    def get_config_history(
        self,
        account_id: str
    ) -> List[Dict[str, Any]]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT config_version, config_json, source, created_at
                FROM configs
                WHERE account_id = ?
                ORDER BY config_version ASC
            """, (account_id,))

            rows = cursor.fetchall()

        return [
            {
                "config_version": r[0],
                "config": json.loads(r[1]),
                "source": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]

    # ==========================================================
    # ROLLBACK TO PREVIOUS VERSION
    # ==========================================================

    def rollback_to_version(
        self,
        account_id: str,
        target_version: int,
        timestamp: str,
    ):

        with self._lock:

            cursor = self._conn.cursor()

            cursor.execute("""
                SELECT config_version
                FROM configs
                WHERE account_id = ?
                AND config_version = ?
            """, (account_id, target_version))

            if not cursor.fetchone():
                raise ConfigRepositoryError("Target version does not exist")

            cursor.execute("""
                INSERT OR REPLACE INTO active_config (
                    account_id,
                    config_version,
                    activated_at
                )
                VALUES (?, ?, ?)
            """, (
                account_id,
                target_version,
                timestamp,
            ))

            self._conn.commit()

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._conn.close()
                self._connection = None