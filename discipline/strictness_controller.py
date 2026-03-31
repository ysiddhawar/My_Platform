from __future__ import annotations

from typing import Dict, Any, Optional

from models.execution_event import ExecutionEvent
from models.account import Account
from models.discipline_report import DisciplineReport
from models.decision_report import DecisionReport


class StrictnessControllerError(Exception):
    pass


class StrictnessController:
    """
    Institutional Strictness Governance Controller

    Responsibilities:
    - Interpret DisciplineReport
    - Apply strict-mode logic
    - Escalate or throttle risk
    - Trigger governance decisions
    - Protect account survival

    This is the final control layer before execution approval.
    """

    def __init__(self):

        # Default thresholds (can be made dynamic later)
        self._block_threshold = 50.0
        self._warning_threshold = 75.0
        self._violation_hard_limit = 3

    # =====================================================
    # MAIN EVALUATION
    # =====================================================

    def evaluate(
        self,
        event: ExecutionEvent,
        account: Account,
        report: DisciplineReport
    ) -> DecisionReport:

        discipline_score = report.discipline_score or 0.0
        violations = report.to_dict().get("violations", [])
        strict_mode = report.strict_mode

        decision_type = "accept"
        approved = True
        recommended_risk_percent = None
        capital_throttle_percent = None
        reason_summary = ""
        recommended_actions = []

        # -------------------------------------------------
        # HARD BLOCK LOGIC
        # -------------------------------------------------

        if strict_mode and (
            discipline_score < self._block_threshold
            or len(violations) >= self._violation_hard_limit
            or report.blocked
        ):

            decision_type = "reject"
            approved = False
            reason_summary = (
                "Trade rejected due to strict mode violation threshold."
            )

        # -------------------------------------------------
        # SOFT WARNING LOGIC
        # -------------------------------------------------

        elif discipline_score < self._warning_threshold:

            decision_type = "throttle"
            approved = True

            # Reduce allowed risk dynamically
            recommended_risk_percent = (
                account.allowed_risk_percent * 0.5
            )

            capital_throttle_percent = 50.0

            reason_summary = (
                "Discipline score low. Risk temporarily reduced."
            )

            recommended_actions.append(
                "Improve checklist compliance before next trade."
            )

        # -------------------------------------------------
        # FULL COMPLIANCE
        # -------------------------------------------------

        else:

            decision_type = "accept"
            approved = True
            reason_summary = "Trade approved. Discipline compliance acceptable."

        # -------------------------------------------------
        # BUILD DECISION REPORT
        # -------------------------------------------------

        decision = DecisionReport(
            entity_type="execution_event",
            entity_id=event.to_dict()["event_id"],
            decision_type=decision_type,
            approved=approved,
            risk_level=account.risk_level,
            confidence_score=discipline_score / 100.0,
            rules_evaluated=report.to_dict().get("rules_evaluated", []),
            rules_passed=report.to_dict().get("rules_passed", []),
            rules_failed=report.to_dict().get("rules_failed", []),
            metrics_snapshot={
                "discipline_score": discipline_score,
                "violations_count": len(violations),
            },
            recommended_risk_percent=recommended_risk_percent,
            capital_throttle_percent=capital_throttle_percent,
            reason_summary=reason_summary,
            recommended_actions=recommended_actions,
        )

        return decision

    # =====================================================
    # CONFIGURATION
    # =====================================================

    def update_thresholds(
        self,
        block_threshold: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        violation_hard_limit: Optional[int] = None,
    ):

        if block_threshold is not None:
            if not (0 <= block_threshold <= 100):
                raise StrictnessControllerError(
                    "block_threshold must be between 0 and 100"
                )
            self._block_threshold = float(block_threshold)

        if warning_threshold is not None:
            if not (0 <= warning_threshold <= 100):
                raise StrictnessControllerError(
                    "warning_threshold must be between 0 and 100"
                )
            self._warning_threshold = float(warning_threshold)

        if violation_hard_limit is not None:
            if violation_hard_limit < 0:
                raise StrictnessControllerError(
                    "violation_hard_limit must be non-negative"
                )
            self._violation_hard_limit = int(violation_hard_limit)