from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------
# Action Types (Deterministic + Platform Compatible)
# ---------------------------------------------------------

ACTION_TYPES = (
    "risk_adjustment",
    "position_size_adjustment",
    "slippage_limit_adjustment",
    "capital_reallocation",
    "strategy_restriction",
    "behavioral_reinforcement",
    "monitoring_instruction",
    "regime_constraint",
    "execution_constraint",
)


def _validate_action_type(action_type: str) -> str:
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Invalid action type: {action_type}")
    return action_type


# ---------------------------------------------------------
# Prescription Instruction (Atomic)
# ---------------------------------------------------------

@dataclass(frozen=True)
class PrescriptionInstruction:
    """
    A single structured prescription instruction.

    Example:
        - Reduce risk per trade to 0.25%
        - Cap max position size to 2 lots
        - Avoid trading between 14:00–16:00
        - Disable strategy 'Breakout_V2'
    """

    action_type: str
    title: str
    description: str
    parameter: Optional[str] = None
    recommended_value: Optional[Any] = None
    current_value: Optional[Any] = None
    applies_to: Optional[str] = None
    auto_applicable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "action_type", _validate_action_type(self.action_type))

        if not self.title:
            raise ValueError("PrescriptionInstruction must have title")

        if not self.description:
            raise ValueError("PrescriptionInstruction must have description")


# ---------------------------------------------------------
# Aggregated AI Prescription Object
# ---------------------------------------------------------

class AIPrescription:
    """
    Institutional-grade structured prescription.

    Responsibilities:
    - Stores structured corrective actions
    - Tracks linkage to diagnosis
    - Supports apply-interpretation workflow
    - Enables compliance tracking
    - Remains deterministic and auditable
    """

    __slots__ = (
        "_prescription_id",
        "_created_at",
        "_diagnosis_id",
        "_instructions",
        "_monitoring_period_days",
        "_requires_user_confirmation",
        "_metadata",
    )

    def __init__(
        self,
        diagnosis_id: str,
        monitoring_period_days: int = 14,
        requires_user_confirmation: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not diagnosis_id:
            raise ValueError("Prescription must reference diagnosis_id")

        self._prescription_id = str(uuid.uuid4())
        self._created_at = time.time()
        self._diagnosis_id = diagnosis_id
        self._instructions: List[PrescriptionInstruction] = []
        self._monitoring_period_days = max(1, monitoring_period_days)
        self._requires_user_confirmation = requires_user_confirmation
        self._metadata = metadata or {}

    # -----------------------------------------------------
    # Add Instruction
    # -----------------------------------------------------

    def add_instruction(self, instruction: PrescriptionInstruction):
        if not isinstance(instruction, PrescriptionInstruction):
            raise TypeError("Invalid instruction type")
        self._instructions.append(instruction)

    # -----------------------------------------------------
    # Applyable Instruction Filter
    # -----------------------------------------------------

    def get_auto_applicable(self) -> List[PrescriptionInstruction]:
        """
        Returns instructions safe for automatic application.
        Used by interpretation_applier.
        """
        return [
            i for i in self._instructions if i.auto_applicable
        ]

    # -----------------------------------------------------
    # Manual Instruction Filter
    # -----------------------------------------------------

    def get_manual_required(self) -> List[PrescriptionInstruction]:
        """
        Returns instructions that require user action.
        """
        return [
            i for i in self._instructions if not i.auto_applicable
        ]

    # -----------------------------------------------------
    # Accessors
    # -----------------------------------------------------

    @property
    def prescription_id(self) -> str:
        return self._prescription_id

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def diagnosis_id(self) -> str:
        return self._diagnosis_id

    @property
    def monitoring_period_days(self) -> int:
        return self._monitoring_period_days

    @property
    def requires_user_confirmation(self) -> bool:
        return self._requires_user_confirmation

    @property
    def instructions(self) -> List[PrescriptionInstruction]:
        return list(self._instructions)

    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)

    # -----------------------------------------------------
    # Structured Export (Platform Compatible)
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prescription_id": self._prescription_id,
            "created_at": self._created_at,
            "diagnosis_id": self._diagnosis_id,
            "monitoring_period_days": self._monitoring_period_days,
            "requires_user_confirmation": self._requires_user_confirmation,
            "instructions": [
                {
                    "action_type": i.action_type,
                    "title": i.title,
                    "description": i.description,
                    "parameter": i.parameter,
                    "recommended_value": i.recommended_value,
                    "current_value": i.current_value,
                    "applies_to": i.applies_to,
                    "auto_applicable": i.auto_applicable,
                    "metadata": i.metadata,
                }
                for i in self._instructions
            ],
            "metadata": self._metadata,
        }

    # -----------------------------------------------------
    # Integrity Validation
    # -----------------------------------------------------

    def validate(self):
        """
        Ensures prescription consistency before application.
        """

        if not self._instructions:
            raise RuntimeError("Prescription contains no instructions")

        for instruction in self._instructions:
            if not isinstance(instruction, PrescriptionInstruction):
                raise RuntimeError("Invalid instruction detected")

        return True