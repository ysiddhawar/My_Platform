from __future__ import annotations

from typing import Dict, Any, List, Optional
from math import exp


class DisciplineScoreEngineError(Exception):
    pass


class DisciplineScoreEngine:
    """
    Institutional Discipline Scoring Engine

    Responsibilities:
    - Compute weighted discipline score
    - Penalize rule failures
    - Penalize behavioral flags
    - Apply violation severity penalties
    - Support recency-based decay (optional)
    - Produce explainable score breakdown

    This engine is deterministic and fully rule-based.
    """

    def __init__(
        self,
        checklist_weight: float = 0.4,
        rules_weight: float = 0.4,
        violation_weight: float = 0.2,
    ):

        total = checklist_weight + rules_weight + violation_weight

        if abs(total - 1.0) > 1e-6:
            raise DisciplineScoreEngineError(
                "Weights must sum to 1.0"
            )

        self._checklist_weight = checklist_weight
        self._rules_weight = rules_weight
        self._violation_weight = violation_weight

    # =====================================================
    # MAIN SCORING
    # =====================================================

    def compute(
        self,
        checklist_completeness: float,
        rules_passed: int,
        rules_failed: int,
        violation_severity_score: Optional[float],
        behavioral_flags: Optional[List[str]] = None,
        recency_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:

        self._validate_inputs(
            checklist_completeness,
            rules_passed,
            rules_failed,
            violation_severity_score
        )

        behavioral_flags = behavioral_flags or []

        # ---------------------------------------------
        # CHECKLIST COMPONENT
        # ---------------------------------------------

        checklist_score = checklist_completeness

        # ---------------------------------------------
        # RULE COMPLIANCE COMPONENT
        # ---------------------------------------------

        total_rules = rules_passed + rules_failed

        if total_rules == 0:
            rule_score = 100.0
        else:
            rule_score = (rules_passed / total_rules) * 100.0

        # ---------------------------------------------
        # VIOLATION PENALTY COMPONENT
        # ---------------------------------------------

        violation_score = 100.0

        if violation_severity_score is not None:
            violation_score -= violation_severity_score

        # Behavioral penalty
        behavioral_penalty = min(len(behavioral_flags) * 5.0, 30.0)
        violation_score -= behavioral_penalty

        violation_score = max(0.0, violation_score)

        # ---------------------------------------------
        # WEIGHTED AGGREGATION
        # ---------------------------------------------

        raw_score = (
            checklist_score * self._checklist_weight +
            rule_score * self._rules_weight +
            violation_score * self._violation_weight
        )

        # ---------------------------------------------
        # RECENCY DECAY ADJUSTMENT (optional)
        # ---------------------------------------------

        decay_factor = 1.0

        if recency_minutes is not None:
            # Exponential decay penalizes rapid repeated violations
            decay_factor = exp(-recency_minutes / 180.0)
            raw_score *= decay_factor

        final_score = round(max(0.0, min(raw_score, 100.0)), 2)

        return {
            "final_score": final_score,
            "components": {
                "checklist_score": round(checklist_score, 2),
                "rule_score": round(rule_score, 2),
                "violation_score": round(violation_score, 2),
                "behavioral_penalty": round(behavioral_penalty, 2),
                "decay_factor": round(decay_factor, 4),
            },
            "weights": {
                "checklist_weight": self._checklist_weight,
                "rules_weight": self._rules_weight,
                "violation_weight": self._violation_weight,
            }
        }

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_inputs(
        self,
        checklist_completeness: float,
        rules_passed: int,
        rules_failed: int,
        violation_severity_score: Optional[float],
    ):

        if not (0 <= checklist_completeness <= 100):
            raise DisciplineScoreEngineError(
                "checklist_completeness must be 0–100"
            )

        if rules_passed < 0 or rules_failed < 0:
            raise DisciplineScoreEngineError(
                "rules_passed and rules_failed must be non-negative"
            )

        if violation_severity_score is not None:
            if not (0 <= violation_severity_score <= 100):
                raise DisciplineScoreEngineError(
                    "violation_severity_score must be 0–100"
                )