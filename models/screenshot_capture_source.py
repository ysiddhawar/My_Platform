from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ScreenshotCaptureSource:
    source_name: str
    source_type: str
    status: str = "active"
    account_ids: List[str] = field(default_factory=list)
    broker_ids: List[str] = field(default_factory=list)
    market_types: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    source_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "status": self.status,
            "account_ids": list(self.account_ids),
            "broker_ids": list(self.broker_ids),
            "market_types": list(self.market_types),
            "capabilities": dict(self.capabilities),
            "created_at": self.created_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ScreenshotCaptureSource":
        return cls(
            source_name=payload["source_name"],
            source_type=payload["source_type"],
            status=payload.get("status", "active"),
            account_ids=payload.get("account_ids", []),
            broker_ids=payload.get("broker_ids", []),
            market_types=payload.get("market_types", []),
            capabilities=payload.get("capabilities", {}),
            source_id=payload.get("source_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
            last_seen_at=datetime.fromisoformat(payload["last_seen_at"]) if payload.get("last_seen_at") else datetime.now(timezone.utc),
        )
