from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TradeRating:
    account_id: str
    trade_id: str
    rating_value: float
    scale_name: str = "five_point"
    rationale: Optional[str] = None
    rated_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    rating_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rating_id": self.rating_id,
            "account_id": self.account_id,
            "trade_id": self.trade_id,
            "rating_value": self.rating_value,
            "scale_name": self.scale_name,
            "rationale": self.rationale,
            "rated_by": self.rated_by,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @property
    def value(self) -> float:
        return self.rating_value

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TradeRating":
        return cls(
            account_id=payload["account_id"],
            trade_id=payload["trade_id"],
            rating_value=payload["rating_value"],
            scale_name=payload.get("scale_name", "five_point"),
            rationale=payload.get("rationale"),
            rated_by=payload.get("rated_by"),
            metadata=payload.get("metadata", {}),
            rating_id=payload.get("rating_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
        )
