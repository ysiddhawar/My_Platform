from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MissedOpportunity:
    account_id: str
    broker_id: str
    symbol: str
    market_type: str
    side: str
    strategy_name: str
    probability_bucket: str
    entry_price: float
    stop_loss_price: float
    target_price: float
    minimum_target_price: Optional[float]
    observed_at: datetime
    timezone_name: str = 'UTC'
    exit_price: Optional[float] = None
    exit_at: Optional[datetime] = None
    exit_reason: Optional[str] = None
    checklist_items: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    opportunity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def _local_observed_at(self) -> datetime:
        return _to_timezone(self.observed_at, self.timezone_name)

    @property
    def local_date(self) -> str:
        return self._local_observed_at().date().isoformat()

    @property
    def local_day_of_week(self) -> str:
        return self._local_observed_at().strftime('%A')

    @property
    def observed_hour(self) -> int:
        return self._local_observed_at().hour

    def _local_exit_at(self) -> Optional[datetime]:
        if self.exit_at is None:
            return None
        return _to_timezone(self.exit_at, self.timezone_name)

    @property
    def exit_date(self) -> Optional[str]:
        local_exit = self._local_exit_at()
        return local_exit.date().isoformat() if local_exit else None

    @property
    def exit_day_of_week(self) -> Optional[str]:
        local_exit = self._local_exit_at()
        return local_exit.strftime('%A') if local_exit else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'opportunity_id': self.opportunity_id,
            'account_id': self.account_id,
            'broker_id': self.broker_id,
            'symbol': self.symbol,
            'market_type': self.market_type,
            'side': self.side,
            'strategy_name': self.strategy_name,
            'probability_bucket': self.probability_bucket,
            'entry_price': self.entry_price,
            'stop_loss_price': self.stop_loss_price,
            'target_price': self.target_price,
            'minimum_target_price': self.minimum_target_price,
            'observed_at': self.observed_at.astimezone(timezone.utc).isoformat(),
            'timezone_name': self.timezone_name,
            'exit_price': self.exit_price,
            'exit_at': self.exit_at.astimezone(timezone.utc).isoformat() if self.exit_at else None,
            'exit_date': self.exit_date,
            'exit_day_of_week': self.exit_day_of_week,
            'exit_reason': self.exit_reason,
            'checklist_items': list(self.checklist_items),
            'notes': self.notes,
            'local_date': self.local_date,
            'local_day_of_week': self.local_day_of_week,
            'observed_hour': self.observed_hour,
            'metadata': dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'MissedOpportunity':
        return cls(
            opportunity_id=payload.get('opportunity_id', str(uuid.uuid4())),
            account_id=payload['account_id'],
            broker_id=payload['broker_id'],
            symbol=payload['symbol'],
            market_type=payload.get('market_type', 'stock'),
            side=payload.get('side', 'buy'),
            strategy_name=payload['strategy_name'],
            probability_bucket=payload['probability_bucket'],
            entry_price=float(payload['entry_price']),
            stop_loss_price=float(payload['stop_loss_price']),
            target_price=float(payload['target_price']),
            minimum_target_price=payload.get('minimum_target_price'),
            observed_at=_coerce_datetime(payload['observed_at']),
            timezone_name=payload.get('timezone_name', 'UTC'),
            exit_price=float(payload['exit_price']) if payload.get('exit_price') is not None else None,
            exit_at=_coerce_datetime(payload.get('exit_at')),
            exit_reason=payload.get('exit_reason'),
            checklist_items=list(payload.get('checklist_items', [])),
            notes=payload.get('notes'),
            metadata=payload.get('metadata', {}),
        )


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value in (None, "", "None", "null"):
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
