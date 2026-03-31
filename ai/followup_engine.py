from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from models.ai_prescription import AIPrescription
from models.ai_followup_report import AIFollowupReport
from models.ai_diagnosis import AIDiagnosis


class FollowupEngineError(Exception):
    pass


class FollowupEngine:
    """
    Institutional Follow-up Engine

    Responsibilities:
    - Compare pre-prescription and post-prescription metrics
    - Detect compliance
    - Detect improvement / deterioration
    - Provide structured follow-up evaluation
    - Remain deterministic and auditable

    This engine:
    - Does NOT recompute metrics
    - Does NOT override governance
    - Only evaluates delta and compliance
    """

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def evaluate(
        self,
        previous_diagnosis: AIDiagnosis,
        previous_prescription: AIPrescription,
        current_metrics: Dict[str, Dict[str, Any]],
        previous_metrics_snapshot: Dict[str, Dict[str, Any]],
        applied_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> AIFollowupReport:

        if not isinstance(previous_prescription, AIPrescription):
            raise FollowupEngineError("Invalid prescription object")

        applied_actions = applied_actions or []

        compliance_score = self._compute_compliance(
            previous_prescription,
            applied_actions,
        )

        metric_delta = self._compute_metric_delta(
            previous_metrics_snapshot,
            current_metrics,
        )

        improvement_score = self._evaluate_improvement(metric_delta)

        status = self._determine_status(
            compliance_score,
            improvement_score,
        )

        return AIFollowupReport(
            timestamp=datetime.now(timezone.utc),
            compliance_score=compliance_score,
            improvement_score=improvement_score,
            metric_delta=metric_delta,
            status=status,
        )

    # ==========================================================
    # COMPLIANCE CHECK
    # ==========================================================

    def _compute_compliance(
        self,
        prescription: AIPrescription,
        applied_actions: List[Dict[str, Any]],
    ) -> float:

        if not prescription.actions:
            return 1.0

        total = len(prescription.actions)
        matched = 0

        for action in prescription.actions:
            if action.get("auto_applicable") is False:
                continue  # user-dependent actions are optional

            for applied in applied_actions:
                if applied.get("type") == action.get("type"):
                    matched += 1
                    break

        return round(matched / total, 2)

    # ==========================================================
    # METRIC DELTA
    # ==========================================================

    def _compute_metric_delta(
        self,
        before: Dict[str, Dict[str, Any]],
        after: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:

        delta = {}

        for category, metrics in before.items():
            if category not in after:
                continue

            delta[category] = {}

            for metric_name, value_before in metrics.items():
                value_after = after.get(category, {}).get(metric_name)

                if isinstance(value_before, (int, float)) and isinstance(value_after, (int, float)):
                    delta_value = value_after - value_before
                    delta[category][metric_name] = delta_value

        return delta

    # ==========================================================
    # IMPROVEMENT EVALUATION
    # ==========================================================

    def _evaluate_improvement(
        self,
        metric_delta: Dict[str, Dict[str, float]],
    ) -> float:

        improvement_score = 0.0
        count = 0

        for category, metrics in metric_delta.items():
            for metric_name, delta in metrics.items():

                # Positive delta treated as improvement
                # (Actual direction logic is enforced by metric_policy_registry)

                if isinstance(delta, (int, float)):
                    improvement_score += delta
                    count += 1

        if count == 0:
            return 0.0

        return round(improvement_score / count, 4)

    # ==========================================================
    # STATUS DETERMINATION
    # ==========================================================

    def _determine_status(
        self,
        compliance_score: float,
        improvement_score: float,
    ) -> str:

        if compliance_score < 0.5:
            return "low_compliance"

        if improvement_score > 0:
            return "improving"

        if improvement_score < 0:
            return "deteriorating"

        return "neutral"
