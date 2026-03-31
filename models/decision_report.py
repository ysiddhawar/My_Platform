from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


class DecisionReportValidationError(Exception):
    pass


class DecisionReport:
    """
    Institutional Governance Decision Snapshot

    Represents:
    - Strategy acceptance / rejection
    - Capital allocation adjustment
    - Risk-level classification result
    - Governance override action

    Used by:
    - decisions/acceptance.py
    - AI interpretation layer
    - Reporting layer
    - Audit trail system
    """

    __slots__ = (
        # Identity
        "_decision_id",
        "_created_at",

        # Scope
        "_entity_type",          # strategy / trade / account / portfolio
        "_entity_id",

        # Classification
        "_risk_level",           # survival / consistency / profitable
        "_previous_risk_level",

        # Decision
        "_decision_type",        # accept / reject / throttle / escalate / downgrade
        "_approved",
        "_confidence_score",

        # Rule Evidence
        "_rules_evaluated",
        "_rules_passed",
        "_rules_failed",

        # Metrics Snapshot
        "_metrics_snapshot",

        # Capital Actions
        "_recommended_risk_percent",
        "_recommended_leverage",
        "_capital_throttle_percent",

        # Explanation
        "_reason_summary",
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
        decision_type: str,
        approved: bool,
        risk_level: Optional[str] = None,
        previous_risk_level: Optional[str] = None,
        confidence_score: Optional[float] = None,
        rules_evaluated: Optional[List[str]] = None,
        rules_passed: Optional[List[str]] = None,
        rules_failed: Optional[List[str]] = None,
        metrics_snapshot: Optional[Dict[str, Any]] = None,
        recommended_risk_percent: Optional[float] = None,
        recommended_leverage: Optional[float] = None,
        capital_throttle_percent: Optional[float] = None,
        reason_summary: Optional[str] = None,
        recommended_actions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self._decision_id = str(uuid.uuid4())
        self._created_at = datetime.now(timezone.utc)

        self._entity_type = self._validate_entity_type(entity_type)
        self._entity_id = self._validate_non_empty(entity_id, "entity_id")

        self._decision_type = self._validate_decision_type(decision_type)
        self._approved = bool(approved)

        self._risk_level = risk_level
        self._previous_risk_level = previous_risk_level

        self._confidence_score = self._validate_confidence(confidence_score)

        self._rules_evaluated = rules_evaluated or []
        self._rules_passed = rules_passed or []
        self._rules_failed = rules_failed or []

        self._metrics_snapshot = metrics_snapshot or {}

        self._recommended_risk_percent = recommended_risk_percent
        self._recommended_leverage = recommended_leverage
        self._capital_throttle_percent = capital_throttle_percent

        self._reason_summary = reason_summary
        self._recommended_actions = recommended_actions or []

        self._metadata = metadata or {}

        self._validate_consistency()

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise DecisionReportValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_entity_type(self, entity_type: str) -> str:
        entity_type = entity_type.lower()
        if entity_type not in ("strategy", "trade", "account", "portfolio"):
            raise DecisionReportValidationError(
                "entity_type must be strategy, trade, account, or portfolio"
            )
        return entity_type

    def _validate_decision_type(self, decision_type: str) -> str:
        decision_type = decision_type.lower()
        if decision_type not in (
            "accept",
            "reject",
            "throttle",
            "escalate",
            "downgrade",
            "upgrade",
        ):
            raise DecisionReportValidationError("Invalid decision_type")
        return decision_type

    def _validate_confidence(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if not isinstance(value, (int, float)) or not (0 <= value <= 1):
            raise DecisionReportValidationError(
                "confidence_score must be between 0 and 1"
            )
        return float(value)

    def _validate_consistency(self):
        if self._approved and self._decision_type == "reject":
            raise DecisionReportValidationError(
                "approved=True inconsistent with decision_type=reject"
            )

    # =====================================================
    # ACCESSORS
    # =====================================================

    @property
    def decision_id(self) -> str:
        return self._decision_id

    @property
    def approved(self) -> bool:
        return self._approved

    @property
    def entity_type(self) -> str:
        return self._entity_type

    @property
    def decision_type(self) -> str:
        return self._decision_type

    # =====================================================
    # EXPORT
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self._decision_id,
            "created_at": self._created_at,
            "entity_type": self._entity_type,
            "entity_id": self._entity_id,
            "risk_level": self._risk_level,
            "previous_risk_level": self._previous_risk_level,
            "decision_type": self._decision_type,
            "approved": self._approved,
            "confidence_score": self._confidence_score,
            "rules_evaluated": self._rules_evaluated,
            "rules_passed": self._rules_passed,
            "rules_failed": self._rules_failed,
            "metrics_snapshot": self._metrics_snapshot,
            "recommended_risk_percent": self._recommended_risk_percent,
            "recommended_leverage": self._recommended_leverage,
            "capital_throttle_percent": self._capital_throttle_percent,
            "reason_summary": self._reason_summary,
            "recommended_actions": self._recommended_actions,
            "metadata": self._metadata,
        }

    def __repr__(self):
        status = "APPROVED" if self._approved else "REJECTED"
        return (
            f"<DecisionReport {self._entity_type.upper()} "
            f"{self._decision_type.upper()} {status}>"
        )