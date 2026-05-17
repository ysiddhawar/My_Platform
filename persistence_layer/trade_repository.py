from __future__ import annotations

import sqlite3
import json
from typing import List, Optional, Dict, Any
from threading import RLock
from pathlib import Path

from models.trade import Trade


class TradeRepositoryError(Exception):
    pass


class TradeRepository:
    """
    Institutional Trade Repository

    Responsibilities:
    - Durable trade persistence
    - Idempotent insert/update
    - Indexed querying
    - Account isolation
    - Snapshot-safe compatibility
    - Metrics-ready retrieval
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "trade_store.db"):

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
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                symbol TEXT,
                market_type TEXT,
                side TEXT,
                entry_data TEXT NOT NULL,
                exit_data TEXT,
                economics_data TEXT,
                behavioral_data TEXT,
                environment_data TEXT,
                system_data TEXT,
                is_closed INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_account
            ON trades (account_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol
            ON trades (symbol)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_closed
            ON trades (is_closed)
        """)

        self._conn.commit()

    # ==========================================================
    # UPSERT TRADE
    # ==========================================================

    def save_trade(self, trade: Trade):

        if not isinstance(trade, Trade):
            raise TradeRepositoryError("Invalid Trade object")

        with self._lock:

            serialized = self._serialize_trade(trade)

            try:
                cursor = self._conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO trades (
                        trade_id,
                        account_id,
                        symbol,
                        market_type,
                        side,
                        entry_data,
                        exit_data,
                        economics_data,
                        behavioral_data,
                        environment_data,
                        system_data,
                        is_closed,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, serialized)

                self._conn.commit()

            except sqlite3.Error as e:
                self._conn.rollback()
                raise TradeRepositoryError(str(e))

    # ==========================================================
    # READ OPERATIONS
    # ==========================================================

    def get_trade(self, trade_id: str) -> Optional[Trade]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM trades WHERE trade_id = ?",
                (trade_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return self._deserialize_trade(row)

    def get_trades_by_account(
        self,
        account_id: str,
        closed_only: Optional[bool] = None,
    ) -> List[Trade]:

        query = "SELECT * FROM trades WHERE account_id = ?"
        params: List[Any] = [account_id]

        if closed_only is True:
            query += " AND is_closed = 1"
        elif closed_only is False:
            query += " AND is_closed = 0"

        query += " ORDER BY created_at ASC"

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._deserialize_trade(r) for r in rows]

    def get_trades_by_symbol(
        self,
        account_id: str,
        symbol: str,
    ) -> List[Trade]:

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                WHERE account_id = ?
                AND symbol = ?
                ORDER BY created_at ASC
            """, (account_id, symbol))

            rows = cursor.fetchall()

        return [self._deserialize_trade(r) for r in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM trades WHERE account_id = ?", (account_id,))
            deleted = cursor.rowcount
            self._conn.commit()
        return deleted

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def _serialize_trade(self, trade: Trade):

        trade_dict = trade.to_dict()
        system_payload = dict(trade_dict.get("system") or {})
        metadata = dict(system_payload.get("metadata") or {})
        metadata.setdefault("broker_id", trade_dict.get("broker_id"))
        metadata.setdefault("strategy_tag", trade_dict.get("strategy") or trade_dict.get("setup_name"))
        metadata.setdefault("setup_name", trade_dict.get("setup_name"))
        system_payload["metadata"] = metadata

        return (
            trade_dict["trade_id"],
            trade_dict["account_id"],
            trade_dict.get("symbol"),
            trade_dict.get("market_type"),
            trade_dict.get("side"),
            json.dumps(trade_dict.get("entry_details")),
            json.dumps(trade_dict.get("exit_details")),
            json.dumps(trade_dict.get("economics")),
            json.dumps(trade_dict.get("behavioral")),
            json.dumps(trade_dict.get("environment")),
            json.dumps(system_payload),
            int(trade_dict.get("is_closed", False)),
            trade_dict.get("created_at"),
            trade_dict.get("updated_at"),
        )

    def _deserialize_trade(self, row):

        columns = [
            "trade_id",
            "account_id",
            "symbol",
            "market_type",
            "side",
            "entry_data",
            "exit_data",
            "economics_data",
            "behavioral_data",
            "environment_data",
            "system_data",
            "is_closed",
            "created_at",
            "updated_at",
        ]

        record = dict(zip(columns, row))

        entry_details = json.loads(record["entry_data"]) if record["entry_data"] else {}
        exit_details = json.loads(record["exit_data"]) if record["exit_data"] else {}
        economics = json.loads(record["economics_data"]) if record["economics_data"] else {}
        behavioral = json.loads(record["behavioral_data"]) if record["behavioral_data"] else {}
        environment = json.loads(record["environment_data"]) if record["environment_data"] else {}
        system = json.loads(record["system_data"]) if record["system_data"] else {}

        entry_details = entry_details or {}
        exit_details = exit_details or {}
        economics = economics or {}
        behavioral = behavioral or {}
        environment = environment or {}
        system = system or {}

        trade_data = {
            "trade_id": record["trade_id"],
            "account_id": record["account_id"],
            "symbol": record["symbol"],
            "market_type": record["market_type"],
            "side": record["side"],
            "is_closed": bool(record["is_closed"]),
            "broker_id": system.get("metadata", {}).get("broker_id", "BROKER"),
            "strategy": system.get("metadata", {}).get("strategy_tag")
            or behavioral.get("pre_trade_capture", {}).get("strategy_name")
            or behavioral.get("strategy_tag")
            or "UNSPECIFIED",
            "setup_name": system.get("metadata", {}).get("setup_name")
            or behavioral.get("pre_trade_capture", {}).get("strategy_name")
            or "UNSPECIFIED",
            "entry_price": entry_details.get("entry_price", 0.0),
            "entry_time": entry_details.get("entry_time") or record["created_at"],
            "stop_loss_at_entry": entry_details.get("stop_loss_at_entry"),
            "target_at_entry": entry_details.get("target_at_entry"),
            "quantity": entry_details.get("quantity", 0.0),
            "lot_size": entry_details.get("lot_size", 1.0),
            "leverage_used": entry_details.get("leverage_used", 1.0),
            "minimum_target_price": entry_details.get("minimum_target_price"),
            "exit_price": exit_details.get("exit_price"),
            "exit_time": exit_details.get("exit_time") or record["updated_at"],
            "exit_reason": exit_details.get("exit_reason"),
            "close_classification": exit_details.get("close_classification"),
            "closed_before_plan": exit_details.get("closed_before_plan", False),
            "gross_pnl": economics.get("gross_pnl"),
            "net_pnl": economics.get("net_pnl"),
            "fees": economics.get("fees", 0.0),
            "commission": economics.get("commission", 0.0),
            "swaps": economics.get("swaps", 0.0),
            "slippage_cost": economics.get("slippage_cost", 0.0),
            "risk_amount": economics.get("risk_amount"),
            "rrr_at_entry": economics.get("rrr_at_entry"),
            "r_multiple": economics.get("r_multiple"),
            "minimum_target_reward": economics.get("required_reward_for_min_target"),
            "checklist_before": behavioral.get("checklist_before", []),
            "checklist_after": behavioral.get("checklist_after", []),
            "probability_bucket": behavioral.get("probability_bucket"),
            "confidence_score": behavioral.get("confidence_score"),
            "emotion_tag": behavioral.get("emotion_tag"),
            "rule_violations_snapshot": behavioral.get("rule_violations_snapshot", []),
            "pre_trade_capture": behavioral.get("pre_trade_capture"),
            "post_trade_capture": behavioral.get("post_trade_capture"),
            "line_history": behavioral.get("line_history", []),
            "notes": behavioral.get("notes"),
            "metadata": system.get("metadata", {}),
            "volatility_regime_at_entry": environment.get("volatility_regime_at_entry"),
            "equity_at_entry": environment.get("equity_at_entry"),
            "drawdown_at_entry": environment.get("drawdown_at_entry"),
            "open_positions_count": environment.get("open_positions_count"),
            "correlation_exposure_snapshot": environment.get("correlation_exposure_snapshot", {}),
        }

        return Trade.from_dict(trade_data)

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def close(self):

        with self._lock:
            if self._connection:
                self._conn.close()
                self._connection: sqlite3.Connection | None = None
