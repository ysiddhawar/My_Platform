from __future__ import annotations

import random
import threading
from typing import Dict, Any, List, Optional


class TailScenarioSimulatorError(Exception):
    pass


class TailScenarioSimulator:
    """
    Institutional Tail Scenario Simulator

    Responsibilities
    ----------------
    • Simulate extreme tail events
    • Inject shocks into equity paths
    • Estimate tail drawdown and ruin risk
    • Remain deterministic-safe and thread-safe
    """

    VERSION = 2

    DEFAULT_SHOCK_MAGNITUDE = 0.30
    DEFAULT_SHOCK_DURATION = 5
    DEFAULT_SCENARIOS = (
        "flash_crash",
        "volatility_spike",
        "liquidity_collapse",
        "correlation_breakdown",
        "black_swan",
    )

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None,
    ):
        self._monitoring_registry = monitoring_registry
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def simulate(
        self,
        equity_paths: List[List[float]],
        shock_magnitude: float = DEFAULT_SHOCK_MAGNITUDE,
        shock_duration: int = DEFAULT_SHOCK_DURATION,
        scenarios: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        if not equity_paths:
            raise TailScenarioSimulatorError("equity_paths required")

        scenarios = scenarios or list(self.DEFAULT_SCENARIOS)

        with self._lock:

            results = {}

            for scenario in scenarios:

                shocked_paths = [
                    self._apply_tail_event(
                        path,
                        scenario,
                        shock_magnitude,
                        shock_duration
                    )
                    for path in equity_paths
                ]

                summary = self._summarize_paths(shocked_paths)

                results[scenario] = {
                    "paths": shocked_paths,
                    "summary": summary
                }

        return results

    # -------------------------------------------------
    # Tail Event Injection
    # -------------------------------------------------

    def _apply_tail_event(
        self,
        path: List[float],
        scenario: str,
        magnitude: float,
        duration: int,
    ) -> List[float]:

        shocked = list(path)

        if len(shocked) <= duration:
            return shocked

        start = random.randint(1, len(shocked) - duration - 1)

        for i in range(start, start + duration):

            if scenario == "flash_crash":
                shocked[i] *= (1 - magnitude)

            elif scenario == "volatility_spike":
                shocked[i] *= (1 + random.uniform(-magnitude, magnitude))

            elif scenario == "liquidity_collapse":
                shocked[i] *= (1 - magnitude * 1.2)

            elif scenario == "correlation_breakdown":
                shocked[i] *= (1 - magnitude * random.uniform(0.5, 1.5))

            elif scenario == "black_swan":
                shocked[i] *= (1 - magnitude * 1.8)

        return shocked

    # -------------------------------------------------
    # Path Summary
    # -------------------------------------------------

    def _summarize_paths(
        self,
        paths: List[List[float]]
    ) -> Dict[str, Any]:

        drawdowns = []
        ruin_count = 0

        for path in paths:

            dd = self._max_drawdown(path)
            drawdowns.append(dd)

            if min(path) <= 0:
                ruin_count += 1

        worst_dd = max(drawdowns)
        avg_dd = sum(drawdowns) / len(drawdowns)

        ruin_prob = ruin_count / len(paths)

        return {
            "worst_tail_drawdown": worst_dd,
            "average_tail_drawdown": avg_dd,
            "tail_ruin_probability": ruin_prob,
            "scenario_paths": len(paths),
        }

    # -------------------------------------------------
    # Drawdown Calculation
    # -------------------------------------------------

    def _max_drawdown(
        self,
        path: List[float]
    ) -> float:

        peak = path[0]
        max_dd = 0.0

        for v in path:

            if v > peak:
                peak = v

            dd = (peak - v) / peak

            if dd > max_dd:
                max_dd = dd

        return max_dd

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "model": "TailScenarioSimulator",
            "version": self.VERSION
        }