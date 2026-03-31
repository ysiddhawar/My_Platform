from __future__ import annotations

from typing import Dict, Any, List, Optional

from models.ai_diagnosis import DiagnosticFinding
from ai.metric_policy_registry import MetricPolicyRegistry
from ai.weakness_analyzer import WeaknessAnalyzer


class MetricInterpreter:
    """
    Fully Adaptive Policy-Driven Metric Interpreter

    - Includes ALL registered metrics automatically
    - No static thresholds
    - Tier-aware governance evaluation
    - Delegates structural reasoning to WeaknessAnalyzer
    - Fully scalable
    - Platform compatible
    """

    def __init__(self):
        self._policy_registry = MetricPolicyRegistry()
        self._weakness_analyzer = WeaknessAnalyzer()

    # -----------------------------------------------------
    # Public Interface
    # -----------------------------------------------------

    def interpret(
        self,
        structured_metrics: Dict[str, Dict[str, Any]],
        governance_tier: str,
        percentiles: Optional[Dict[str, float]] = None,
        zscores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, List[DiagnosticFinding]]:

        weaknesses: List[DiagnosticFinding] = []
        strengths: List[DiagnosticFinding] = []

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
                weaknesses.append(
                    DiagnosticFinding(
                        category=policy.category,
                        title=f"{metric_name} below required level",
                        description=(
                            f"{metric_name} does not meet "
                            f"{governance_tier} tier criteria."
                        ),
                        severity="high",
                        metric_reference=metric_name,
                        value=value,
                        threshold=policy.tier_thresholds.get(governance_tier),
                    )
                )

            elif result == "pass":
                strengths.append(
                    DiagnosticFinding(
                        category=policy.category,
                        title=f"{metric_name} meets required level",
                        description=(
                            f"{metric_name} satisfies "
                            f"{governance_tier} tier governance requirement."
                        ),
                        severity="info",
                        metric_reference=metric_name,
                        value=value,
                        threshold=policy.tier_thresholds.get(governance_tier),
                    )
                )

        # Cross-layer structural analysis
        cross_layer_findings = self._weakness_analyzer.analyze(
            structured_metrics=structured_metrics,
            governance_tier=governance_tier,
            percentiles=percentiles,
            zscores=zscores,
        )

        weaknesses.extend(cross_layer_findings)

        return {
            "weaknesses": weaknesses,
            "strengths": strengths,
        }

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