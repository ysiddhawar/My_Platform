from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.missed_opportunity import MissedOpportunity


class MissedOpportunityRepositoryError(Exception):
    pass


class MissedOpportunityRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = 'missed_opportunities.db'):
        self._lock = RLock()
        self._db_path = Path(db_path)
        self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
        self._connection.execute('PRAGMA journal_mode=WAL;')
        self._connection.execute('PRAGMA synchronous=FULL;')
        self._create_schema()

    def _create_schema(self):
        with self._lock:
            self._connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS missed_opportunities (
                    opportunity_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    opportunity_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                '''
            )
            self._connection.execute(
                'CREATE INDEX IF NOT EXISTS idx_missed_opportunities_account_day ON missed_opportunities (account_id, local_date)'
            )
            self._connection.execute(
                'CREATE INDEX IF NOT EXISTS idx_missed_opportunities_strategy ON missed_opportunities (account_id, strategy_name)'
            )
            self._connection.commit()

    def save_opportunity(self, opportunity: MissedOpportunity):
        payload = opportunity.to_dict()
        with self._lock:
            self._connection.execute(
                '''
                INSERT OR REPLACE INTO missed_opportunities (
                    opportunity_id, account_id, local_date, strategy_name, opportunity_json, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    payload['opportunity_id'],
                    payload['account_id'],
                    payload['local_date'],
                    payload['strategy_name'],
                    json.dumps(payload),
                    self.SCHEMA_VERSION,
                ),
            )
            self._connection.commit()

    def get_opportunity(self, opportunity_id: str) -> Optional[MissedOpportunity]:
        with self._lock:
            row = self._connection.execute(
                'SELECT opportunity_json FROM missed_opportunities WHERE opportunity_id = ?',
                (opportunity_id,),
            ).fetchone()
        return MissedOpportunity.from_dict(json.loads(row[0])) if row else None

    def list_by_account(self, account_id: str) -> List[MissedOpportunity]:
        with self._lock:
            rows = self._connection.execute(
                'SELECT opportunity_json FROM missed_opportunities WHERE account_id = ? ORDER BY local_date ASC, opportunity_id ASC',
                (account_id,),
            ).fetchall()
        return [MissedOpportunity.from_dict(json.loads(row[0])) for row in rows]

    def list_by_account_for_day(self, account_id: str, local_date: str) -> List[MissedOpportunity]:
        with self._lock:
            rows = self._connection.execute(
                'SELECT opportunity_json FROM missed_opportunities WHERE account_id = ? AND local_date = ? ORDER BY opportunity_id ASC',
                (account_id, local_date),
            ).fetchall()
        return [MissedOpportunity.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                'DELETE FROM missed_opportunities WHERE account_id = ?',
                (account_id,),
            )
            deleted = cursor.rowcount
            self._connection.commit()
        return deleted

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
