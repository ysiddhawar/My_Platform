from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ScreenshotCaptureRequest:
    account_id: str
    trade_id: str
    broker_id: Optional[str]
    market_type: Optional[str]
    symbol: str
    status: str = "pending"
    trigger: str = "trade_closed"
    requested_by: str = "system"
    source_hint: Optional[str] = None
    claimed_by: Optional[str] = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "account_id": self.account_id,
            "trade_id": self.trade_id,
            "broker_id": self.broker_id,
            "market_type": self.market_type,
            "symbol": self.symbol,
            "status": self.status,
            "trigger": self.trigger,
            "requested_by": self.requested_by,
            "source_hint": self.source_hint,
            "claimed_by": self.claimed_by,
            "requested_at": self.requested_at.isoformat(),
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failure_reason": self.failure_reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ScreenshotCaptureRequest":
        return cls(
            account_id=payload["account_id"],
            trade_id=payload["trade_id"],
            broker_id=payload.get("broker_id"),
            market_type=payload.get("market_type"),
            symbol=payload["symbol"],
            status=payload.get("status", "pending"),
            trigger=payload.get("trigger", "trade_closed"),
            requested_by=payload.get("requested_by", "system"),
            source_hint=payload.get("source_hint"),
            claimed_by=payload.get("claimed_by"),
            requested_at=datetime.fromisoformat(payload["requested_at"]) if payload.get("requested_at") else datetime.now(timezone.utc),
            claimed_at=datetime.fromisoformat(payload["claimed_at"]) if payload.get("claimed_at") else None,
            completed_at=datetime.fromisoformat(payload["completed_at"]) if payload.get("completed_at") else None,
            failure_reason=payload.get("failure_reason"),
            metadata=payload.get("metadata", {}),
            request_id=payload.get("request_id", str(uuid.uuid4())),
        )
