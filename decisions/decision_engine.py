from __future__ import annotations

from typing import Dict, Any, Optional

from decisions.governance_levels import GovernanceLevels
from decisions.capital_governor import CapitalGovernor
from decisions.strategy_approval import StrategyApproval
from decisions.deployment_validator import DeploymentValidator


class DecisionEngineError(Exception):
    pass


class DecisionEngine:
    """
    Institutional Decision Orchestrator

    Responsibilities:
    - Orchestrate governance classification
    - Generate capital advisory
    - Generate strategy advisory
    - Generate deployment advisory
    - Produce unified structured output
    - NEVER restrict execution
    - Deterministic + replay-safe
    """

    VERSION = 1

    def __init__(
        self,
        governance_levels: Optional[GovernanceLevels] = None,
        capital_governor: Optional[CapitalGovernor] = None,
        strategy_approval: Optional[StrategyApproval] = None,
        deployment_validator: Optional[DeploymentValidator] = None,
    ):
        self._governance_levels = governance_levels or GovernanceLevels()
        self._capital_governor = capital_governor or CapitalGovernor()
        self._strategy_approval = strategy_approval or StrategyApproval()
        self._deployment_validator = deployment_validator or DeploymentValidator()

    # ---------------------------------------------------------
    # PUBLIC ENTRY
    # ---------------------------------------------------------

    def evaluate(
        self,
        structured_data: Dict[str, Dict[str, Any]],
        base_capital: float,
        ai_diagnosis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        if not isinstance(structured_data, dict):
            raise DecisionEngineError("structured_data must be dict")

        if base_capital <= 0:
            raise DecisionEngineError("base_capital must be positive")

        # -----------------------------------------------------
        # 1️⃣ Governance Classification
        # -----------------------------------------------------

        governance_result = self._governance_levels.classify(
            structured_data
        )

        # -----------------------------------------------------
        # 2️⃣ Capital Advisory
        # -----------------------------------------------------

        capital_advisory = self._capital_governor.generate_advisory(
            governance_result=governance_result,
            structured_data=structured_data,
            base_capital=base_capital,
        )

        # -----------------------------------------------------
        # 3️⃣ Strategy Advisory
        # -----------------------------------------------------

        strategy_advisory = self._strategy_approval.evaluate(
            structured_data=structured_data,
            governance_result=governance_result,
            ai_diagnosis=ai_diagnosis,
        )

        # -----------------------------------------------------
        # 4️⃣ Deployment Advisory
        # -----------------------------------------------------

        deployment_advisory = self._deployment_validator.evaluate(
            structured_data=structured_data,
            governance_result=governance_result,
            capital_advisory=capital_advisory,
        )

        # -----------------------------------------------------
        # Unified Decision Output
        # -----------------------------------------------------

        return {
            "version": self.VERSION,
            "governance": governance_result,
            "capital_advisory": capital_advisory,
            "strategy_advisory": strategy_advisory,
            "deployment_advisory": deployment_advisory,
            "ai_diagnosis_used": ai_diagnosis is not None,
            "advisory_only": True,
        }