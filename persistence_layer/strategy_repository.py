from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from models.strategy import Strategy


class StrategyRepositoryError(Exception):
    pass


class StrategyRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "strategy_store.db"):
        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
        )
        self._connection.execute("PRAGMA journal_mode=WAL;")
        self._connection.execute("PRAGMA synchronous=FULL;")
        self._initialize()

    def _initialize(self):
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    strategy_json TEXT NOT NULL,
                    is_active INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_strategy_active
                ON strategies (is_active)
                """
            )
            self._connection.commit()

    def save_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        data = strategy.to_dict()
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO strategies (
                    strategy_id,
                    name,
                    strategy_json,
                    is_active,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["strategy_id"],
                    data["name"],
                    json.dumps(data),
                    int(data["is_active"]),
                    data["metadata"].get("created_at", datetime.now(timezone.utc).isoformat()),
                ),
            )
            self._connection.commit()
        return data

    def list_strategies(self, active_only: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT strategy_json FROM strategies"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name ASC"
        with self._lock:
            rows = self._connection.execute(query).fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_strategy(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._connection.execute(
                "SELECT strategy_json FROM strategies WHERE name = ?",
                (name,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def append_checklist_items(
        self,
        strategy_name: str,
        checklist_items: List[str],
        mandatory_items: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        existing = self.get_strategy(strategy_name)
        if not existing:
            raise StrategyRepositoryError("Strategy not found")

        merged_items = list(dict.fromkeys(existing.get("checklist_items", []) + checklist_items))
        merged_mandatory = list(
            dict.fromkeys(existing.get("mandatory_checklist_items", []) + (mandatory_items or []))
        )

        strategy = Strategy(
            name=existing.get("name", "UNNAMED"),
            description=existing.get("description", ""),
            market_types=existing.get("market_types", []),
            checklist_items=merged_items,
            mandatory_checklist_items=merged_mandatory,
            risk_profile=existing.get("risk_profile"),
            acceptance_rules=existing.get("acceptance_rules"),
            rejection_rules=existing.get("rejection_rules"),
            level_classification_rules=existing.get("level_classification_rules"),
            default_risk_percent=existing.get("default_risk_percent", 1.0),
            max_risk_percent=existing.get("max_risk_percent", 2.0),
            is_active=existing.get("is_active", True),
            metadata=existing.get("metadata"),
        )
        return self.save_strategy(strategy)

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
