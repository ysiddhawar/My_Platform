from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class DisciplineReportValidationError(Exception):
    pass


class DisciplineReport:
    """
    Institutional Discipline Governance Snapshot

    Represents:
    - Checklist compliance result
    - Rule violations detected
    - Strict mode enforcement result
    - Behavioral flags
    - Discipline scoring outcome

    Used by:
    - discipline/rules_engine.py
    - execution_gatekeeper
    - strictness_controller
    - AI interpretation layer
    - reporting layer
    """

    __slots__ = (
        # Identity
        "_report_id",
        "_created_at",

        # Scope
        "_entity_type",      # execution_event / trade
        "_entity_id",

        # Strategy Context
        "_strategy_tag",
        "_setup_name",

        # Checklist Evaluation
        "_selected_checklist",
        "_mandatory_checklist",
        "_missing_mandatory",
        "_invalid_items",

        # Rule Evaluation
        "_rules_evaluated",
        "_rules_passed",
        "_rules_failed",

        # Violations
        "_violations",
        "_violation_severity_score",

        # Behavioral Flags
        "_behavioral_flags",  # e.g. FOMO, Overtrading, Rule Skipping

        # Strict Mode Result
        "_strict_mode",
        "_blocked",

        # Scoring
        "_discipline_score",

        # Explanation
        "_summary",
        "_recommended_actions",

        # System
        "_metadata",
    )

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        strategy_tag: str,
        setup_name: str,
        selected_checklist: Optional[List[str]] = None,
        mandatory_checklist: Optional[List[str]] = None,
        missing_mandatory: Optional[List[str]] = None,
        invalid_items: Optional[List[str]] = None,
        rules_evaluated: Optional[List[str]] = None,
        rules_passed: Optional[List[str]] = None,
        rules_failed: Optional[List[str]] = None,
        violations: Optional[List[str]] = None,
        violation_severity_score: Optional[float] = None,
        behavioral_flags: Optional[List[str]] = None,
        strict_mode: bool = False,
        blocked: bool = False,
        discipline_score: Optional[float] = None,
        summary: Optional[str] = None,
        recommended_actions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self._report_id = str(uuid.uuid4())
        self._created_at = datetime.now(timezone.utc)

        self._entity_type = self._validate_entity_type(entity_type)
        self._entity_id = self._validate_non_empty(entity_id, "entity_id")

        self._strategy_tag = self._validate_non_empty(strategy_tag, "strategy_tag")
        self._setup_name = self._validate_non_empty(setup_name, "setup_name")

        self._selected_checklist = selected_checklist or []
        self._mandatory_checklist = mandatory_checklist or []
        self._missing_mandatory = missing_mandatory or []
        self._invalid_items = invalid_items or []

        self._rules_evaluated = rules_evaluated or []
        self._rules_passed = rules_passed or []
        self._rules_failed = rules_failed or []

        self._violations = violations or []
        self._violation_severity_score = self._validate_optional_percentage(
            violation_severity_score, "violation_severity_score"
        )

        self._behavioral_flags = behavioral_flags or []

        self._strict_mode = bool(strict_mode)
        self._blocked = bool(blocked)

        self._discipline_score = self._validate_optional_percentage(
            discipline_score, "discipline_score"
        )

        self._summary = summary
        self._recommended_actions = recommended_actions or []

        self._metadata = metadata or {}

        self._validate_consistency()

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise DisciplineReportValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_entity_type(self, entity_type: str) -> str:
        entity_type = entity_type.lower()
        if entity_type not in ("execution_event", "trade"):
            raise DisciplineReportValidationError(
                "entity_type must be execution_event or trade"
            )
        return entity_type

    def _validate_optional_percentage(
        self,
        value: Optional[float],
        field: str
    ) -> Optional[float]:

        if value is None:
            return None

        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            raise DisciplineReportValidationError(
                f"{field} must be between 0 and 100"
            )

        return float(value)

    def _validate_consistency(self):

        if self._blocked and not self._strict_mode:
            raise DisciplineReportValidationError(
                "blocked=True requires strict_mode=True"
            )

    # =====================================================
    # ACCESSORS
    # =====================================================

    @property
    def report_id(self) -> str:
        return self._report_id

    @property
    def discipline_score(self) -> Optional[float]:
        return self._discipline_score

    @property
    def blocked(self) -> bool:
        return self._blocked

    @property
    def strict_mode(self) -> bool:
        return self._strict_mode

    # =====================================================
    # EXPORT
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self._report_id,
            "created_at": self._created_at,
            "entity_type": self._entity_type,
            "entity_id": self._entity_id,
            "strategy_tag": self._strategy_tag,
            "setup_name": self._setup_name,
            "selected_checklist": self._selected_checklist,
            "mandatory_checklist": self._mandatory_checklist,
            "missing_mandatory": self._missing_mandatory,
            "invalid_items": self._invalid_items,
            "rules_evaluated": self._rules_evaluated,
            "rules_passed": self._rules_passed,
            "rules_failed": self._rules_failed,
            "violations": self._violations,
            "violation_severity_score": self._violation_severity_score,
            "behavioral_flags": self._behavioral_flags,
            "strict_mode": self._strict_mode,
            "blocked": self._blocked,
            "discipline_score": self._discipline_score,
            "summary": self._summary,
            "recommended_actions": self._recommended_actions,
            "metadata": self._metadata,
        }

    def __repr__(self):
        status = "BLOCKED" if self._blocked else "ALLOWED"
        return (
            f"<DisciplineReport {self._strategy_tag} "
            f"{status} Score={self._discipline_score}>"
        )