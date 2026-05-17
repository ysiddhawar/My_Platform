from __future__ import annotations

from typing import Dict, Any, Optional


class StrategyApprovalError(Exception):
    pass


class StrategyApproval:
    """
    Institutional Strategy Advisory Engine

    Responsibilities:
    - Evaluate structural quality of strategy
    - Provide continuation / modification guidance
    - Detect fragility patterns
    - NEVER restrict execution
    - Deterministic + replay-safe
    """

    VERSION = 1

    # ---------------------------------------------------------
    # PUBLIC ENTRY
    # ---------------------------------------------------------

    def evaluate(
        self,
        structured_data: Dict[str, Dict[str, Any]],
        governance_result: Dict[str, Any],
        ai_diagnosis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        if not isinstance(structured_data, dict):
            raise StrategyApprovalError("structured_data must be dict")

        tier = governance_result.get("tier")
        score = governance_result.get("score", 0)

        # Type narrowing: ensure tier and score match expected types
        if tier is None or not isinstance(tier, str):
            tier = "unknown"
        if not isinstance(score, (int, float)):
            score = 0.0

        metrics = structured_data.get("metrics", {})
        robustness = structured_data.get("robustness", {})
        stress = structured_data.get("stress", {})
        survival = structured_data.get("survival", {})

        structural_flags = self._detect_structural_risks(
            metrics,
            robustness,
            stress,
            survival,
        )

        recommendation = self._generate_recommendation(
            tier,
            score,
            structural_flags,
        )

        return {
            "version": self.VERSION,
            "tier": tier,
            "governance_score": score,
            "structural_flags": structural_flags,
            "recommendation": recommendation,
            "advisory_only": True,
        }

    # ---------------------------------------------------------
    # STRUCTURAL RISK DETECTION
    # ---------------------------------------------------------

    def _detect_structural_risks(
        self,
        metrics: Dict[str, Any],
        robustness: Dict[str, Any],
        stress: Dict[str, Any],
        survival: Dict[str, Any],
    ) -> Dict[str, Any]:

        flags = {}

        # Performance fragility
        sharpe = metrics.get("performance", {}).get("sharpe", 0)
        if sharpe < 0.7:
            flags["weak_risk_adjusted_return"] = True

        # High drawdown
        max_dd = metrics.get("risk", {}).get("max_drawdown", 1)
        if max_dd > 0.35:
            flags["excessive_drawdown"] = True

        # Robustness instability
        stability = robustness.get("stability_score", 0)
        if stability < 0.4:
            flags["low_structural_stability"] = True

        # Stress vulnerability
        stress_score = stress.get("stress_score", 0)
        if stress_score > 0.7:
            flags["high_stress_sensitivity"] = True

        # Survival danger
        risk_of_ruin = survival.get("risk_of_ruin", 0)
        if risk_of_ruin > 0.15:
            flags["elevated_ruin_probability"] = True

        return flags

    # ---------------------------------------------------------
    # RECOMMENDATION GENERATION
    # ---------------------------------------------------------

    def _generate_recommendation(
        self,
        tier: str,
        score: float,
        flags: Dict[str, Any],
    ) -> Dict[str, Any]:

        if tier == "dying":
            return {
                "status": "high_risk_structure",
                "action": "Major structural revision recommended.",
                "continue_trading": True,
                "risk_expectation": "High probability of capital erosion if unchanged.",
            }

        if tier == "survival":
            return {
                "status": "capital_preservation_phase",
                "action": "Focus on drawdown control and risk discipline.",
                "continue_trading": True,
                "risk_expectation": "Moderate fragility under stress conditions.",
            }

        if tier == "consistency":
            return {
                "status": "stable_structure",
                "action": "Continue with incremental refinement.",
                "continue_trading": True,
                "risk_expectation": "Reasonable structural resilience.",
            }

        if tier == "profitable":
            return {
                "status": "institutional_structure",
                "action": "Maintain structure. Optimize capital efficiency.",
                "continue_trading": True,
                "risk_expectation": "Strong structural stability.",
            }

        return {
            "status": "unknown",
            "action": "Further review required.",
            "continue_trading": True,
            "risk_expectation": "Uncertain structural condition.",
        }