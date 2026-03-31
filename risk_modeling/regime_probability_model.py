from __future__ import annotations

import math
import threading
from typing import Dict, Any, Optional


class RegimeProbabilityModelError(Exception):
    pass


class RegimeProbabilityModel:
    """
    Institutional Regime Probability Model

    Responsibilities
    ----------------
    • Estimate probabilities of trading regimes
    • Combine signals from risk, survival, robustness, and regime metrics
    • Provide normalized regime probability distribution
    • Remain deterministic and thread-safe
    """

    VERSION = 2

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None
    ):
        self._monitoring_registry = monitoring_registry
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def estimate(
        self,
        metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:

        if not isinstance(metrics, dict):
            raise RegimeProbabilityModelError("metrics must be dict")

        with self._lock:

            risk_metrics = metrics.get("risk", {})
            regime_metrics = metrics.get("regimes", {})
            survival_metrics = metrics.get("survival", {})
            robustness_metrics = metrics.get("robustness", {})
            portfolio_metrics = metrics.get("portfolio", {})

            volatility_signal = self._volatility_signal(
                risk_metrics,
                regime_metrics
            )

            drawdown_signal = self._drawdown_signal(
                risk_metrics,
                survival_metrics
            )

            fragility_signal = self._fragility_signal(
                robustness_metrics,
                regime_metrics,
                portfolio_metrics
            )

            return self._compute_probabilities(
                volatility_signal,
                drawdown_signal,
                fragility_signal
            )

    # -------------------------------------------------
    # Volatility Signal
    # -------------------------------------------------

    def _volatility_signal(
        self,
        risk_metrics: Dict[str, Any],
        regime_metrics: Dict[str, Any],
    ) -> float:

        rolling_vol = float(risk_metrics.get("rolling_volatility", 0.0))
        adaptive_vol = float(risk_metrics.get("adaptive_rolling_volatility", 0.0))
        garch_vol = float(regime_metrics.get("garch_volatility", 0.0))

        # Weighted volatility estimate
        score = (
            0.45 * rolling_vol +
            0.35 * adaptive_vol +
            0.20 * garch_vol
        )

        return max(score, 0.0)

    # -------------------------------------------------
    # Drawdown Signal
    # -------------------------------------------------

    def _drawdown_signal(
        self,
        risk_metrics: Dict[str, Any],
        survival_metrics: Dict[str, Any],
    ) -> float:

        max_dd = float(risk_metrics.get("max_drawdown", 0.0))
        dd_percentile = float(survival_metrics.get("drawdown_percentile", 0.0))
        survival_score = float(survival_metrics.get("survival_score", 1.0))

        score = (
            0.5 * max_dd +
            0.3 * dd_percentile +
            0.2 * (1 - survival_score)
        )

        return max(score, 0.0)

    # -------------------------------------------------
    # Fragility Signal
    # -------------------------------------------------

    def _fragility_signal(
        self,
        robustness_metrics: Dict[str, Any],
        regime_metrics: Dict[str, Any],
        portfolio_metrics: Dict[str, Any],
    ) -> float:

        stability_score = float(robustness_metrics.get("stability_score", 1.0))
        regime_fragility = float(regime_metrics.get("regime_fragility", 0.0))
        portfolio_fragility = float(
            portfolio_metrics.get("portfolio_fragility_index", 0.0)
        )

        fragility = (
            0.5 * regime_fragility +
            0.3 * portfolio_fragility +
            0.2 * (1 - stability_score)
        )

        return max(fragility, 0.0)

    # -------------------------------------------------
    # Probability Calculation
    # -------------------------------------------------

    def _compute_probabilities(
        self,
        volatility_signal: float,
        drawdown_signal: float,
        fragility_signal: float,
    ) -> Dict[str, float]:

        scores = {
            "low_volatility": -volatility_signal,
            "normal_volatility": -abs(volatility_signal - 0.5),
            "high_volatility": volatility_signal,
            "drawdown_regime": drawdown_signal,
            "crash_regime": drawdown_signal * fragility_signal,
            "stable_performance": -fragility_signal,
            "fragile_performance": fragility_signal,
        }

        probs = self._softmax(scores)

        return probs

    # -------------------------------------------------
    # Softmax Normalization
    # -------------------------------------------------

    def _softmax(
        self,
        scores: Dict[str, float]
    ) -> Dict[str, float]:

        max_score = max(scores.values())

        exp_scores = {
            k: math.exp(v - max_score)
            for k, v in scores.items()
        }

        total = sum(exp_scores.values())

        if total == 0:
            return {k: 0.0 for k in scores}

        return {
            k: v / total
            for k, v in exp_scores.items()
        }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "model": "RegimeProbabilityModel",
            "version": self.VERSION
        }