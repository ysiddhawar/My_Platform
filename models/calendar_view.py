from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CalendarColorState:
    key: str
    color: str
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "color": self.color,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CalendarColorState":
        return cls(
            key=payload["key"],
            color=payload["color"],
            label=payload.get("label"),
        )


@dataclass(frozen=True)
class CalendarDaySummary:
    account_id: str
    day: str
    pnl: float = 0.0
    gross_pnl: float = 0.0
    total_cost: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    total_platform_time_minutes: float = 0.0
    platform_session_count: int = 0
    missed_opportunity_count: int = 0
    discipline_score: Optional[float] = None
    state_key: Optional[str] = None
    notes_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "day": self.day,
            "pnl": self.pnl,
            "gross_pnl": self.gross_pnl,
            "total_cost": self.total_cost,
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "total_platform_time_minutes": self.total_platform_time_minutes,
            "platform_session_count": self.platform_session_count,
            "missed_opportunity_count": self.missed_opportunity_count,
            "discipline_score": self.discipline_score,
            "state_key": self.state_key,
            "notes_count": self.notes_count,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CalendarDaySummary":
        return cls(
            account_id=payload["account_id"],
            day=payload["day"],
            pnl=payload.get("pnl", 0.0),
            gross_pnl=payload.get("gross_pnl", 0.0),
            total_cost=payload.get("total_cost", 0.0),
            trade_count=payload.get("trade_count", 0),
            win_count=payload.get("win_count", 0),
            loss_count=payload.get("loss_count", 0),
            total_platform_time_minutes=payload.get("total_platform_time_minutes", 0.0),
            platform_session_count=payload.get("platform_session_count", 0),
            missed_opportunity_count=payload.get("missed_opportunity_count", 0),
            discipline_score=payload.get("discipline_score"),
            state_key=payload.get("state_key"),
            notes_count=payload.get("notes_count", 0),
            metadata=payload.get("metadata", {}),
        )
