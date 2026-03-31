from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DashboardWidget:
    widget_key: str
    title: str
    position: Dict[str, int]
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "widget_key": self.widget_key,
            "title": self.title,
            "position": dict(self.position),
            "config": dict(self.config),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DashboardWidget":
        return cls(
            widget_key=payload["widget_key"],
            title=payload["title"],
            position=payload.get("position", {}),
            config=payload.get("config", {}),
        )


@dataclass(frozen=True)
class DashboardLayout:
    account_id: str
    dashboard_name: str
    template_name: Optional[str] = None
    widgets: List[DashboardWidget] = field(default_factory=list)
    theme_overrides: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    layout_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "account_id": self.account_id,
            "dashboard_name": self.dashboard_name,
            "template_name": self.template_name,
            "widgets": [widget.to_dict() for widget in self.widgets],
            "theme_overrides": dict(self.theme_overrides),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DashboardLayout":
        return cls(
            account_id=payload["account_id"],
            dashboard_name=payload["dashboard_name"],
            template_name=payload.get("template_name"),
            widgets=[DashboardWidget.from_dict(item) for item in payload.get("widgets", [])],
            theme_overrides=payload.get("theme_overrides", {}),
            metadata=payload.get("metadata", {}),
            layout_id=payload.get("layout_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else datetime.now(timezone.utc),
        )
