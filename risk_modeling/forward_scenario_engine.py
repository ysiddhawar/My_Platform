from __future__ import annotations

import random
import threading
from typing import Dict, Any, List, Optional


class ForwardScenarioEngineError(Exception):
    pass


class ForwardScenarioEngine:
    """
    Institutional forward scenario simulator.

    Produces multiple equity paths from historical returns using bootstrapping.
    """

    VERSION = 1

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None,
    ):
        self._monitoring_registry = monitoring_registry
        self._lock = threading.Lock()

    def simulate(
        self,
        returns: List[float],
        initial_equity: float,
        num_paths: int = 200,
        horizon: Optional[int] = None,
    ) -> Dict[str, Any]:

        if not returns:
            raise ForwardScenarioEngineError("returns required")

        if initial_equity <= 0:
            raise ForwardScenarioEngineError("initial_equity must be positive")

        horizon = horizon or len(returns)
        if horizon <= 0:
            raise ForwardScenarioEngineError("horizon must be positive")

        with self._lock:
            equity_paths: List[List[float]] = []

            for _ in range(num_paths):
                equity = initial_equity
                path = [equity]

                for _ in range(horizon):
                    r = random.choice(returns)
                    equity = max(0.0, equity * (1.0 + float(r)))
                    path.append(equity)

                equity_paths.append(path)

            finals = [p[-1] for p in equity_paths]
            avg_final = sum(finals) / len(finals)
            best_final = max(finals)
            worst_final = min(finals)

            summary = {
                "path_count": len(equity_paths),
                "horizon": horizon,
                "average_final_equity": avg_final,
                "best_final_equity": best_final,
                "worst_final_equity": worst_final,
            }

            return {
                "equity_paths": equity_paths,
                "summary": summary,
            }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "engine": "ForwardScenarioEngine",
            "version": self.VERSION,
        }
