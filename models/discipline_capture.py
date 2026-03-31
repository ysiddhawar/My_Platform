from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DisciplineCapture:
    phase: str
    strategy_name: str
    probability_bucket: str
    selected_checklist: List[str] = field(default_factory=list)
    mandatory_checklist: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "strategy_name": self.strategy_name,
            "probability_bucket": self.probability_bucket,
            "selected_checklist": list(self.selected_checklist),
            "mandatory_checklist": list(self.mandatory_checklist),
            "all_criteria_selected": set(self.mandatory_checklist).issubset(
                set(self.selected_checklist)
            ) if self.mandatory_checklist else False,
            "notes": self.notes,
            "captured_at": self.captured_at.isoformat(),
            "metadata": dict(self.metadata),
        }
