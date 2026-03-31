from __future__ import annotations

from typing import Dict, Any


class DeploymentValidatorError(Exception):
    pass


class DeploymentValidator:
    """
    Institutional Deployment Advisory Engine

    Responsibilities:
    - Evaluate deployment structural readiness
    - Detect live fragility conditions
    - Generate advisory deployment risk profile
    - NEVER block execution
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
        capital_advisory: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(structured_data, dict):
            raise DeploymentValidatorError("structured_data must be dict")

        tier = governance_result.get("tier")
        score = governance_result.get("score", 0.0)

        survival = structured_data.get("survival", {})
        stress = structured_data.get("stress", {})
        robustness = structured_data.get("robustness", {})
        risk_control = structured_data.get("risk_control", {})

        deployment_flags = self._detect_deployment_risks(
            survival,
            stress,
            robustness,
            risk_control,
        )

        deployment_profile = self._generate_profile(
            tier,
            score,
            deployment_flags,
            capital_advisory,
        )

        return {
            "version": self.VERSION,
            "tier": tier,
            "governance_score": score,
            "deployment_flags": deployment_flags,
            "deployment_profile": deployment_profile,
            "advisory_only": True,
        }

    # ---------------------------------------------------------
    # DEPLOYMENT RISK DETECTION
    # ---------------------------------------------------------

    def _detect_deployment_risks(
        self,
        survival: Dict[str, Any],
        stress: Dict[str, Any],
        robustness: Dict[str, Any],
        risk_control: Dict[str, Any],
    ) -> Dict[str, bool]:

        flags = {}

        # High ruin probability
        if survival.get("risk_of_ruin", 0) > 0.15:
            flags["high_ruin_probability"] = True

        # Fragile under stress
        if stress.get("stress_score", 0) > 0.75:
            flags["stress_fragility"] = True

        # Weak Monte Carlo stability
        if robustness.get("monte_carlo_stability", 0) < 0.4:
            flags["monte_carlo_instability"] = True

        # Weak regime stability
        if robustness.get("regime_stability", 0) < 0.4:
            flags["regime_instability"] = True

        # Weak kill switch configuration
        if risk_control.get("kill_switch_score", 1) < 0.5:
            flags["weak_risk_control_layer"] = True

        return flags

    # ---------------------------------------------------------
    # DEPLOYMENT PROFILE GENERATION
    # ---------------------------------------------------------

    def _generate_profile(
        self,
        tier: str,
        score: float,
        flags: Dict[str, bool],
        capital_advisory: Dict[str, Any],
    ) -> Dict[str, Any]:

        recommended_capital = capital_advisory.get("recommended_capital")

        if tier == "dying":
            return {
                "deployment_status": "extreme_risk",
                "live_expectation": "High probability of accelerated capital decay.",
                "recommended_capital": recommended_capital,
                "live_monitoring_required": True,
            }

        if tier == "survival":
            return {
                "deployment_status": "fragile",
                "live_expectation": "Capital preservation possible, but sensitive to volatility shocks.",
                "recommended_capital": recommended_capital,
                "live_monitoring_required": True,
            }

        if tier == "consistency":
            return {
                "deployment_status": "moderate_stability",
                "live_expectation": "Reasonable live stability if discipline maintained.",
                "recommended_capital": recommended_capital,
                "live_monitoring_required": False,
            }

        if tier == "profitable":
            return {
                "deployment_status": "structurally_stable",
                "live_expectation": "Strong live performance expectancy under controlled leverage.",
                "recommended_capital": recommended_capital,
                "live_monitoring_required": False,
            }

        return {
            "deployment_status": "unknown",
            "live_expectation": "Uncertain structural profile.",
            "recommended_capital": recommended_capital,
            "live_monitoring_required": True,
        }