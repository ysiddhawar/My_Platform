from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

from models.ai_diagnosis import DiagnosticFinding
from ai.metric_policy_registry import MetricPolicyRegistry


class WeaknessAnalyzer:
    """
    Fully Adaptive Cross-Metric Weakness Analyzer

    - Includes ALL registered metrics
    - No static thresholds
    - Tier-aware governance evaluation
    - Policy-driven
    - Scalable to future metrics automatically
    """

    def __init__(self):
        self._policy_registry = MetricPolicyRegistry()

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def analyze(
        self,
        structured_metrics: Dict[str, Dict[str, Any]],
        governance_tier: str,
        percentiles: Optional[Dict[str, float]] = None,
        zscores: Optional[Dict[str, float]] = None,
    ) -> List[DiagnosticFinding]:

        findings: List[DiagnosticFinding] = []

        flat_metrics = self._flatten(structured_metrics)

        for metric_name, value in flat_metrics.items():

            policy = self._policy_registry.get_policy(metric_name)
            if not policy:
                continue

            percentile = percentiles.get(metric_name) if percentiles else None
            zscore = zscores.get(metric_name) if zscores else None

            result = self._policy_registry.evaluate(
                metric_name=metric_name,
                value=value,
                tier=governance_tier,
                percentile=percentile,
                zscore=zscore,
            )

            if result == "fail":
                findings.append(
                    DiagnosticFinding(
                        category=policy.category,
                        title=f"{metric_name} below required tier level",
                        description=(
                            f"{metric_name} does not meet "
                            f"{governance_tier} tier governance criteria."
                        ),
                        severity="high",
                        metric_reference=metric_name,
                        value=value,
                        threshold=policy.tier_thresholds.get(governance_tier),
                    )
                )

        return findings

    # -----------------------------------------------------
    # Internal Utilities
    # -----------------------------------------------------

    def _flatten(
        self,
        structured_metrics: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:

        flat: Dict[str, float] = {}

        for category_dict in structured_metrics.values():
            if not isinstance(category_dict, dict):
                continue

            for key, value in category_dict.items():
                if isinstance(value, (int, float)):
                    flat[key] = float(value)

        return flat