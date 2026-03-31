from __future__ import annotations

import threading
from typing import Dict, Any, Optional, List

from risk_modeling.forward_scenario_engine import ForwardScenarioEngine
from risk_modeling.regime_probability_model import RegimeProbabilityModel
from risk_modeling.forward_drawdown_estimator import ForwardDrawdownEstimator
from risk_modeling.forward_ruin_probability import ForwardRuinProbability
from risk_modeling.tail_scenario_simulator import TailScenarioSimulator


class RiskModelingEngineError(Exception):
    pass


class RiskModelingEngine:
    """
    Institutional Forward Risk Modeling Engine

    Responsibilities
    ----------------
    • Orchestrate all forward risk models
    • Produce unified forward risk analysis
    • Remain deterministic and thread-safe
    """

    VERSION = 1

    def __init__(
        self,
        scenario_engine: Optional[ForwardScenarioEngine] = None,
        regime_model: Optional[RegimeProbabilityModel] = None,
        drawdown_estimator: Optional[ForwardDrawdownEstimator] = None,
        ruin_model: Optional[ForwardRuinProbability] = None,
        tail_simulator: Optional[TailScenarioSimulator] = None,
        monitoring_registry: Optional[Any] = None,
    ):

        self._scenario_engine = scenario_engine or ForwardScenarioEngine()
        self._regime_model = regime_model or RegimeProbabilityModel()
        self._drawdown_estimator = drawdown_estimator or ForwardDrawdownEstimator()
        self._ruin_model = ruin_model or ForwardRuinProbability()
        self._tail_simulator = tail_simulator or TailScenarioSimulator()

        self._monitoring_registry = monitoring_registry

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def analyze(
        self,
        metrics: Dict[str, Dict[str, Any]],
        returns: List[float],
        initial_equity: float,
    ) -> Dict[str, Any]:

        if not isinstance(metrics, dict):
            raise RiskModelingEngineError("metrics must be dict")

        if not returns:
            raise RiskModelingEngineError("returns required")

        if initial_equity <= 0:
            raise RiskModelingEngineError("initial_equity must be positive")

        with self._lock:

            # -----------------------------------------
            # 1️⃣ Regime Probabilities
            # -----------------------------------------

            regimes = self._regime_model.estimate(metrics)

            # -----------------------------------------
            # 2️⃣ Forward Scenario Simulation
            # -----------------------------------------

            scenario_result = self._scenario_engine.simulate(
                returns=returns,
                initial_equity=initial_equity,
            )

            equity_paths = scenario_result["equity_paths"]

            # -----------------------------------------
            # 3️⃣ Drawdown Forecast
            # -----------------------------------------

            drawdown_forecast = self._drawdown_estimator.estimate(
                equity_paths
            )

            # -----------------------------------------
            # 4️⃣ Ruin Forecast
            # -----------------------------------------

            ruin_forecast = self._ruin_model.estimate(
                equity_paths,
                initial_equity=initial_equity
            )

            # -----------------------------------------
            # 5️⃣ Tail Risk Simulation
            # -----------------------------------------

            tail_risk = self._tail_simulator.simulate(
                equity_paths
            )

            # -----------------------------------------
            # 6️⃣ Unified Report
            # -----------------------------------------

            return {
                "regime_probabilities": regimes,
                "scenario_summary": scenario_result["summary"],
                "drawdown_forecast": drawdown_forecast,
                "ruin_forecast": ruin_forecast,
                "tail_risk": tail_risk,
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "engine": "RiskModelingEngine",
            "version": self.VERSION,
            "modules": {
                "scenario_engine": self._scenario_engine.VERSION,
                "regime_model": self._regime_model.VERSION,
                "drawdown_estimator": self._drawdown_estimator.VERSION,
                "ruin_model": self._ruin_model.VERSION,
                "tail_simulator": self._tail_simulator.VERSION,
            },
        }