from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import List, Optional

from models.trading_platform_session import TradingPlatformSession


class TradingPlatformSessionRepositoryError(Exception):
    pass


class TradingPlatformSessionRepository:
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = 'trading_platform_sessions.db'):
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
                CREATE TABLE IF NOT EXISTS trading_platform_sessions (
                    session_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    session_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL
                )
                '''
            )
            self._connection.execute(
                'CREATE INDEX IF NOT EXISTS idx_platform_sessions_account_day ON trading_platform_sessions (account_id, local_date)'
            )
            self._connection.commit()

    def save_session(self, session: TradingPlatformSession):
        payload = session.to_dict()
        with self._lock:
            self._connection.execute(
                '''
                INSERT OR REPLACE INTO trading_platform_sessions (
                    session_id, account_id, local_date, session_json, schema_version
                ) VALUES (?, ?, ?, ?, ?)
                ''',
                (payload['session_id'], payload['account_id'], payload['local_date'], json.dumps(payload), self.SCHEMA_VERSION),
            )
            self._connection.commit()

    def get_session(self, session_id: str) -> Optional[TradingPlatformSession]:
        with self._lock:
            row = self._connection.execute(
                'SELECT session_json FROM trading_platform_sessions WHERE session_id = ?',
                (session_id,),
            ).fetchone()
        return TradingPlatformSession.from_dict(json.loads(row[0])) if row else None

    def list_by_account(self, account_id: str) -> List[TradingPlatformSession]:
        with self._lock:
            rows = self._connection.execute(
                'SELECT session_json FROM trading_platform_sessions WHERE account_id = ? ORDER BY local_date ASC, session_id ASC',
                (account_id,),
            ).fetchall()
        return [TradingPlatformSession.from_dict(json.loads(row[0])) for row in rows]

    def list_by_account_for_day(self, account_id: str, local_date: str) -> List[TradingPlatformSession]:
        with self._lock:
            rows = self._connection.execute(
                'SELECT session_json FROM trading_platform_sessions WHERE account_id = ? AND local_date = ? ORDER BY session_id ASC',
                (account_id, local_date),
            ).fetchall()
        return [TradingPlatformSession.from_dict(json.loads(row[0])) for row in rows]

    def list_open_sessions(self, account_id: Optional[str] = None) -> List[TradingPlatformSession]:
        query = 'SELECT session_json FROM trading_platform_sessions'
        params = []
        if account_id:
            query += ' WHERE account_id = ?'
            params.append(account_id)
            query += ' AND '
        else:
            query += ' WHERE '
        query += 'json_extract(session_json, "$.closed_at") IS NULL ORDER BY local_date ASC, session_id ASC'
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [TradingPlatformSession.from_dict(json.loads(row[0])) for row in rows]

    def delete_by_account(self, account_id: str) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                'DELETE FROM trading_platform_sessions WHERE account_id = ?',
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
