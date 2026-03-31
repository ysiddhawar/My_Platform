from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------
# Compliance Status Types
# ---------------------------------------------------------

COMPLIANCE_STATUS = (
    "not_applicable",
    "not_followed",
    "partially_followed",
    "followed",
)


def _validate_compliance(status: str) -> str:
    if status not in COMPLIANCE_STATUS:
        raise ValueError(f"Invalid compliance status: {status}")
    return status


# ---------------------------------------------------------
# Instruction Follow-up Evaluation (Atomic)
# ---------------------------------------------------------

@dataclass(frozen=True)
class InstructionFollowup:
    """
    Represents evaluation of a single prescription instruction
    after monitoring period.
    """

    instruction_id: str
    compliance_status: str
    performance_before: Optional[Dict[str, Any]] = None
    performance_after: Optional[Dict[str, Any]] = None
    improvement_score: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(
            self,
            "compliance_status",
            _validate_compliance(self.compliance_status),
        )

        if not self.instruction_id:
            raise ValueError("InstructionFollowup must reference instruction_id")


# ---------------------------------------------------------
# AI Follow-Up Report (Aggregated)
# ---------------------------------------------------------

class AIFollowupReport:
    """
    Institutional-grade follow-up report.

    Responsibilities:
    - Links to prescription
    - Tracks compliance per instruction
    - Measures improvement
    - Produces compliance score
    - Produces improvement score
    - Remains deterministic and auditable
    """

    __slots__ = (
        "_followup_id",
        "_created_at",
        "_prescription_id",
        "_diagnosis_id",
        "_instruction_followups",
        "_overall_compliance_score",
        "_overall_improvement_score",
        "_metadata",
    )

    def __init__(
        self,
        prescription_id: str,
        diagnosis_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not prescription_id:
            raise ValueError("Followup must reference prescription_id")

        if not diagnosis_id:
            raise ValueError("Followup must reference diagnosis_id")

        self._followup_id = str(uuid.uuid4())
        self._created_at = time.time()
        self._prescription_id = prescription_id
        self._diagnosis_id = diagnosis_id
        self._instruction_followups: List[InstructionFollowup] = []
        self._overall_compliance_score: Optional[float] = None
        self._overall_improvement_score: Optional[float] = None
        self._metadata = metadata or {}

    # -----------------------------------------------------
    # Add Instruction Followup
    # -----------------------------------------------------

    def add_instruction_followup(self, followup: InstructionFollowup):
        if not isinstance(followup, InstructionFollowup):
            raise TypeError("Invalid followup type")
        self._instruction_followups.append(followup)

    # -----------------------------------------------------
    # Compliance Score (Deterministic)
    # -----------------------------------------------------

    def compute_overall_compliance(self) -> float:
        """
        Computes compliance score based on instruction adherence.
        """

        if not self._instruction_followups:
            self._overall_compliance_score = 0.0
            return self._overall_compliance_score

        weights = {
            "not_applicable": 0.0,
            "not_followed": 0.0,
            "partially_followed": 0.5,
            "followed": 1.0,
        }

        total = sum(weights[f.compliance_status] for f in self._instruction_followups)
        score = (total / len(self._instruction_followups)) * 100.0

        self._overall_compliance_score = round(score, 2)
        return self._overall_compliance_score

    # -----------------------------------------------------
    # Improvement Score (Deterministic)
    # -----------------------------------------------------

    def compute_overall_improvement(self) -> float:
        """
        Aggregates improvement scores from instruction evaluations.
        """

        improvements = [
            f.improvement_score
            for f in self._instruction_followups
            if f.improvement_score is not None
        ]

        if not improvements:
            self._overall_improvement_score = 0.0
            return self._overall_improvement_score

        score = sum(improvements) / len(improvements)
        self._overall_improvement_score = round(score, 2)
        return self._overall_improvement_score

    # -----------------------------------------------------
    # Accessors
    # -----------------------------------------------------

    @property
    def followup_id(self) -> str:
        return self._followup_id

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def prescription_id(self) -> str:
        return self._prescription_id

    @property
    def diagnosis_id(self) -> str:
        return self._diagnosis_id

    @property
    def instruction_followups(self) -> List[InstructionFollowup]:
        return list(self._instruction_followups)

    @property
    def overall_compliance_score(self) -> Optional[float]:
        return self._overall_compliance_score

    @property
    def overall_improvement_score(self) -> Optional[float]:
        return self._overall_improvement_score

    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)

    # -----------------------------------------------------
    # Structured Export
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "followup_id": self._followup_id,
            "created_at": self._created_at,
            "prescription_id": self._prescription_id,
            "diagnosis_id": self._diagnosis_id,
            "overall_compliance_score": self._overall_compliance_score,
            "overall_improvement_score": self._overall_improvement_score,
            "instructions": [
                {
                    "instruction_id": f.instruction_id,
                    "compliance_status": f.compliance_status,
                    "performance_before": f.performance_before,
                    "performance_after": f.performance_after,
                    "improvement_score": f.improvement_score,
                    "notes": f.notes,
                    "metadata": f.metadata,
                }
                for f in self._instruction_followups
            ],
            "metadata": self._metadata,
        }

    # -----------------------------------------------------
    # Integrity Validation
    # -----------------------------------------------------

    def validate(self):
        """
        Ensures structural integrity before persistence or evaluation.
        """

        if not self._instruction_followups:
            raise RuntimeError("Followup report has no instruction evaluations")

        for f in self._instruction_followups:
            if not isinstance(f, InstructionFollowup):
                raise RuntimeError("Invalid followup entry detected")

        return True