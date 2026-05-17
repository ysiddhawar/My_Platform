from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from threading import RLock
from typing import Optional, List, Dict, Any

from models.account import Account


class AccountRepositoryError(Exception):
    pass


class AccountRepository:
    """
    Institutional Account Repository

    Responsibilities:
    - Persist Account domain objects
    - Track equity & capital evolution
    - Maintain governance tier
    - Enable survival-layer rebuild
    - Support recovery engine
    - Provide idempotent upsert
    - Provide audit-ready capital history
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "account_store.db"):

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

        # Core account table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                account_data_json TEXT NOT NULL,
                governance_tier TEXT,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Capital history table (audit-grade)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capital_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                equity REAL NOT NULL,
                balance REAL NOT NULL,
                drawdown REAL,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_account_history
            ON capital_history (account_id)
        """)

        self._conn.commit()

    # ==========================================================
    # UPSERT ACCOUNT
    # ==========================================================

    def save(self, account: Account):

        if not isinstance(account, Account):
            raise AccountRepositoryError("Invalid Account object")

        with self._lock:

            data = account.to_dict()

            payload = (
                data["account_id"],
                json.dumps(data),
                data.get("governance_tier"),
                self.SCHEMA_VERSION,
                data["created_at"],
                data["updated_at"],
            )

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO accounts (
                        account_id,
                        account_data_json,
                        governance_tier,
                        schema_version,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, payload)

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise AccountRepositoryError(str(e))

    # ==========================================================
    # ACCOUNT RETRIEVAL
    # ==========================================================

    def get(self, account_id: str) -> Optional[Account]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT account_data_json FROM accounts WHERE account_id = ?",
                (account_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        return Account.from_dict(data)

    def get_all_accounts(self) -> List[Account]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT account_data_json FROM accounts")
            rows = cursor.fetchall()

        return [Account.from_dict(json.loads(r[0])) for r in rows]

    # ==========================================================
    # CAPITAL HISTORY
    # ==========================================================

    def append_capital_snapshot(
        self,
        account_id: str,
        equity: float,
        balance: float,
        drawdown: Optional[float],
        timestamp: str,
    ):

        with self._lock:

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT INTO capital_history (
                        account_id,
                        equity,
                        balance,
                        drawdown,
                        timestamp
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    account_id,
                    equity,
                    balance,
                    drawdown,
                    timestamp
                ))

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise AccountRepositoryError(str(e))

    def get_capital_history(
        self,
        account_id: str
    ) -> List[Dict[str, Any]]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT equity, balance, drawdown, timestamp
                FROM capital_history
                WHERE account_id = ?
                ORDER BY timestamp ASC
            """, (account_id,))
            rows = cursor.fetchall()

        return [
            {
                "equity": r[0],
                "balance": r[1],
                "drawdown": r[2],
                "timestamp": r[3],
            }
            for r in rows
        ]

    # ==========================================================
    # GOVERNANCE TIER UPDATE
    # ==========================================================

    def update_governance_tier(
        self,
        account_id: str,
        new_tier: str,
        timestamp: str
    ):

        with self._lock:

            cursor = self._conn.cursor()

            cursor.execute("""
                UPDATE accounts
                SET governance_tier = ?,
                    updated_at = ?
                WHERE account_id = ?
            """, (new_tier, timestamp, account_id))

            self._conn.commit()

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._conn.close()
                self._connection: sqlite3.Connection | None = None