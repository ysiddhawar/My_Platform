from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TradeTag:
    account_id: str
    name: str
    category: str
    color: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tag_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "account_id": self.account_id,
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "description": self.description,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @property
    def name_value(self) -> str:
        return self.name

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TradeTag":
        return cls(
            account_id=payload["account_id"],
            name=payload["name"],
            category=payload["category"],
            color=payload.get("color"),
            description=payload.get("description"),
            metadata=payload.get("metadata", {}),
            tag_id=payload.get("tag_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
        )
