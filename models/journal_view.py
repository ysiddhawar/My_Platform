from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class JournalFilterPreset:
    name: str
    filters: Dict[str, Any] = field(default_factory=dict)
    visible_columns: List[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    sort_direction: str = "desc"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "filters": dict(self.filters),
            "visible_columns": list(self.visible_columns),
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JournalFilterPreset":
        return cls(
            name=payload["name"],
            filters=payload.get("filters", {}),
            visible_columns=payload.get("visible_columns", []),
            sort_by=payload.get("sort_by"),
            sort_direction=payload.get("sort_direction", "desc"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(frozen=True)
class JournalViewConfig:
    account_id: str
    default_columns: List[str] = field(default_factory=list)
    saved_filters: List[JournalFilterPreset] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    view_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_id": self.view_id,
            "account_id": self.account_id,
            "default_columns": list(self.default_columns),
            "saved_filters": [preset.to_dict() for preset in self.saved_filters],
            "search_fields": list(self.search_fields),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JournalViewConfig":
        return cls(
            account_id=payload["account_id"],
            default_columns=payload.get("default_columns", []),
            saved_filters=[JournalFilterPreset.from_dict(item) for item in payload.get("saved_filters", [])],
            search_fields=payload.get("search_fields", []),
            metadata=payload.get("metadata", {}),
            view_id=payload.get("view_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
        )
