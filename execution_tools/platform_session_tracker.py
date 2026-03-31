from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, Optional

from models.trading_platform_session import TradingPlatformSession
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository


class PlatformSessionTrackerError(Exception):
    pass


class PlatformSessionTracker:
    def __init__(self, session_repository: TradingPlatformSessionRepository):
        self._session_repository = session_repository
        self._lock = RLock()
        self._active_sessions: Dict[str, TradingPlatformSession] = {}

    def open_session(
        self,
        account_id: str,
        broker_id: str,
        platform_name: str,
        timezone_name: str = 'UTC',
        opened_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            existing = self._active_sessions.get(account_id) or self._recover_open_session(account_id)
            if existing is not None:
                self._active_sessions[account_id] = existing
                return existing.to_dict()

            session = TradingPlatformSession(
                account_id=account_id,
                broker_id=broker_id,
                platform_name=platform_name,
                opened_at=opened_at or datetime.now(timezone.utc),
                timezone_name=timezone_name,
                metadata=metadata or {},
            )
            self._session_repository.save_session(session)
            self._active_sessions[account_id] = session
            return session.to_dict()

    def close_session(
        self,
        account_id: str,
        closed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._active_sessions.pop(account_id, None) or self._recover_open_session(account_id)
            if session is None:
                return None

            merged_metadata = dict(session.metadata)
            merged_metadata.update(metadata or {})
            closed_session = TradingPlatformSession(
                session_id=session.session_id,
                account_id=session.account_id,
                broker_id=session.broker_id,
                platform_name=session.platform_name,
                opened_at=session.opened_at,
                closed_at=closed_at or datetime.now(timezone.utc),
                timezone_name=session.timezone_name,
                metadata=merged_metadata,
            )
            self._session_repository.save_session(closed_session)
            return closed_session.to_dict()

    def get_active_session(self, account_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._active_sessions.get(account_id) or self._recover_open_session(account_id)
            if session is not None:
                self._active_sessions[account_id] = session
            return session.to_dict() if session else None

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            for session in self._session_repository.list_open_sessions():
                self._active_sessions.setdefault(session.account_id, session)
            return {account_id: session.to_dict() for account_id, session in self._active_sessions.items()}

    def _recover_open_session(self, account_id: str) -> Optional[TradingPlatformSession]:
        sessions = self._session_repository.list_open_sessions(account_id=account_id)
        if not sessions:
            return None
        return sessions[-1]
