from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TradingPlatformSession:
    account_id: str
    broker_id: str
    platform_name: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    timezone_name: str = 'UTC'
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def _local_opened_at(self) -> datetime:
        return _to_timezone(self.opened_at, self.timezone_name)

    def _local_closed_at(self) -> Optional[datetime]:
        if self.closed_at is None:
            return None
        return _to_timezone(self.closed_at, self.timezone_name)

    @property
    def local_date(self) -> str:
        return self._local_opened_at().date().isoformat()

    @property
    def local_day_of_week(self) -> str:
        return self._local_opened_at().strftime('%A')

    @property
    def start_hour(self) -> int:
        return self._local_opened_at().hour

    @property
    def end_hour(self) -> Optional[int]:
        local_closed_at = self._local_closed_at()
        return local_closed_at.hour if local_closed_at else None

    @property
    def duration_minutes(self) -> float:
        effective_closed_at = self.closed_at or datetime.now(timezone.utc)
        delta = effective_closed_at - self.opened_at
        minutes = max(delta.total_seconds(), 0.0) / 60.0
        return round(min(minutes, 1440.0), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'account_id': self.account_id,
            'broker_id': self.broker_id,
            'platform_name': self.platform_name,
            'opened_at': self.opened_at.astimezone(timezone.utc).isoformat(),
            'closed_at': self.closed_at.astimezone(timezone.utc).isoformat() if self.closed_at else None,
            'timezone_name': self.timezone_name,
            'local_date': self.local_date,
            'local_day_of_week': self.local_day_of_week,
            'start_hour': self.start_hour,
            'end_hour': self.end_hour,
            'duration_minutes': self.duration_minutes,
            'metadata': dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'TradingPlatformSession':
        return cls(
            session_id=payload.get('session_id', str(uuid.uuid4())),
            account_id=payload['account_id'],
            broker_id=payload['broker_id'],
            platform_name=payload.get('platform_name', 'trading_platform'),
            opened_at=_coerce_datetime(payload['opened_at']),
            closed_at=_coerce_datetime(payload.get('closed_at')),
            timezone_name=payload.get('timezone_name', 'UTC'),
            metadata=payload.get('metadata', {}),
        )


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _to_timezone(value: datetime, timezone_name: str) -> datetime:
    tz = _resolve_timezone(timezone_name)
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(tz)


def _resolve_timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name or "UTC")
    except Exception:
        return timezone.utc
