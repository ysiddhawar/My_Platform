from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class JournalNote:
    account_id: str
    note_type: str
    title: str
    body: str
    trade_id: Optional[str] = None
    note_date: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    note_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "note_id": self.note_id,
            "account_id": self.account_id,
            "note_type": self.note_type,
            "title": self.title,
            "body": self.body,
            "trade_id": self.trade_id,
            "note_date": self.note_date,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def body_text(self) -> str:
        return self.body

    @property
    def title_text(self) -> str:
        return self.title

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JournalNote":
        return cls(
            account_id=payload["account_id"],
            note_type=payload["note_type"],
            title=payload["title"],
            body=payload["body"],
            trade_id=payload.get("trade_id"),
            note_date=payload.get("note_date"),
            tags=payload.get("tags", []),
            metadata=payload.get("metadata", {}),
            note_id=payload.get("note_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else datetime.now(timezone.utc),
        )
