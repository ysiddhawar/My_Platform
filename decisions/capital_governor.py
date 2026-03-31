from __future__ import annotations

from typing import Dict, Any


class CapitalGovernorError(Exception):
    pass


class CapitalGovernor:
    """
    Institutional Capital Advisory Engine

    Responsibilities:
    - Translate governance tier into capital advisory policy
    - Compute risk scaling suggestions
    - Generate advisory config patch
    - NEVER enforce restrictions
    - Remain deterministic and replay-safe
    """

    VERSION = 1

    # --------------------------------------------------------
    # PUBLIC ENTRY
    # --------------------------------------------------------

    def generate_advisory(
        self,
        governance_result: Dict[str, Any],
        structured_data: Dict[str, Dict[str, Any]],
        base_capital: float,
    ) -> Dict[str, Any]:
        """
        Produce advisory capital guidance.

        Does NOT enforce anything.
        Returns recommendation only.
        """

        if not isinstance(governance_result, dict):
            raise CapitalGovernorError("Invalid governance_result")

        if not isinstance(structured_data, dict):
            raise CapitalGovernorError("Invalid structured_data")

        tier = governance_result.get("tier")
        score = governance_result.get("score", 0.0)

        if base_capital <= 0:
            raise CapitalGovernorError("base_capital must be positive")

        scaling_factor = self._determine_scaling_factor(tier, score)

        advisory_capital = base_capital * scaling_factor

        advisory_limits = self._generate_risk_guidance(
            tier,
            structured_data,
        )

        return {
            "version": self.VERSION,
            "tier": tier,
            "governance_score": score,
            "recommended_capital": advisory_capital,
            "capital_scaling_factor": scaling_factor,
            "risk_guidance": advisory_limits,
            "advisory_only": True,
        }

    # --------------------------------------------------------
    # CAPITAL SCALING LOGIC
    # --------------------------------------------------------

    def _determine_scaling_factor(
        self,
        tier: str,
        score: float,
    ) -> float:

        if tier == "dying":
            return 0.25

        if tier == "survival":
            return 0.5 + (score / 200)

        if tier == "consistency":
            return 1.0 + (score - 65) / 100

        if tier == "profitable":
            return 1.5 + (score - 80) / 80

        return 0.5

    # --------------------------------------------------------
    # RISK GUIDANCE GENERATION
    # --------------------------------------------------------

    def _generate_risk_guidance(
        self,
        tier: str,
        structured_data: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:

        metrics = structured_data.get("metrics", {})
        survival = structured_data.get("survival", {})
        risk_control = structured_data.get("risk_control", {})

        risk_of_ruin = survival.get("risk_of_ruin", 0.5)
        max_drawdown = metrics.get("risk", {}).get("max_drawdown", 0.5)

        # Advisory only — no enforcement
        if tier == "dying":
            return {
                "suggested_max_risk_percent": 0.002,
                "suggested_max_daily_drawdown": 0.01,
                "suggested_max_consecutive_losses": 3,
                "cooldown_recommended": True,
            }

        if tier == "survival":
            return {
                "suggested_max_risk_percent": 0.005,
                "suggested_max_daily_drawdown": 0.02,
                "suggested_max_consecutive_losses": 4,
                "cooldown_recommended": risk_of_ruin > 0.1,
            }

        if tier == "consistency":
            return {
                "suggested_max_risk_percent": 0.01,
                "suggested_max_daily_drawdown": 0.03,
                "suggested_max_consecutive_losses": 5,
                "cooldown_recommended": False,
            }

        if tier == "profitable":
            return {
                "suggested_max_risk_percent": 0.015,
                "suggested_max_daily_drawdown": 0.04,
                "suggested_max_consecutive_losses": 6,
                "cooldown_recommended": False,
            }

        return {
            "suggested_max_risk_percent": 0.005,
        }