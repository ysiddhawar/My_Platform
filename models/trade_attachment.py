from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AttachmentMarker:
    label: str
    price: Optional[float] = None
    timestamp: Optional[str] = None
    color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "price": self.price,
            "timestamp": self.timestamp,
            "color": self.color,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AttachmentMarker":
        return cls(
            label=payload["label"],
            price=payload.get("price"),
            timestamp=payload.get("timestamp"),
            color=payload.get("color"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(frozen=True)
class TradeAttachment:
    account_id: str
    trade_id: str
    attachment_type: str
    file_name: str
    storage_path: str
    source: str
    broker_id: Optional[str] = None
    market_type: Optional[str] = None
    content_type: Optional[str] = None
    description: Optional[str] = None
    is_auto_captured: bool = False
    markers: List[AttachmentMarker] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "account_id": self.account_id,
            "trade_id": self.trade_id,
            "attachment_type": self.attachment_type,
            "file_name": self.file_name,
            "storage_path": self.storage_path,
            "source": self.source,
            "broker_id": self.broker_id,
            "market_type": self.market_type,
            "content_type": self.content_type,
            "description": self.description,
            "is_auto_captured": self.is_auto_captured,
            "markers": [marker.to_dict() for marker in self.markers],
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TradeAttachment":
        return cls(
            account_id=payload["account_id"],
            trade_id=payload["trade_id"],
            attachment_type=payload["attachment_type"],
            file_name=payload["file_name"],
            storage_path=payload["storage_path"],
            source=payload["source"],
            broker_id=payload.get("broker_id"),
            market_type=payload.get("market_type"),
            content_type=payload.get("content_type"),
            description=payload.get("description"),
            is_auto_captured=payload.get("is_auto_captured", False),
            markers=[AttachmentMarker.from_dict(item) for item in payload.get("markers", [])],
            metadata=payload.get("metadata", {}),
            attachment_id=payload.get("attachment_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
        )
