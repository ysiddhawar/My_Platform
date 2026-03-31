from __future__ import annotations

import threading
from typing import Dict, Any, List, Optional


class ForwardRuinProbabilityError(Exception):
    pass


class ForwardRuinProbability:
    """
    Institutional Forward Ruin Probability Engine

    Responsibilities
    ----------------
    • Estimate probability of account ruin
    • Estimate kill-switch trigger probability
    • Estimate survival probability
    • Estimate survival horizon
    • Remain deterministic and thread-safe
    """

    VERSION = 1

    DEFAULT_RUIN_THRESHOLD = 0.0

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
        equity_paths: List[List[float]],
        initial_equity: float,
        kill_switch_threshold: Optional[float] = None,
        ruin_threshold: float = DEFAULT_RUIN_THRESHOLD,
    ) -> Dict[str, Any]:

        if not equity_paths:
            raise ForwardRuinProbabilityError("equity_paths required")

        if initial_equity <= 0:
            raise ForwardRuinProbabilityError("initial_equity must be positive")

        ruin_count = 0
        kill_switch_count = 0
        survival_steps: List[int] = []

        for path in equity_paths:

            ruin_hit = False
            kill_switch_hit = False

            for step, value in enumerate(path):

                if value <= ruin_threshold:
                    ruin_hit = True
                    survival_steps.append(step)
                    break

                if kill_switch_threshold is not None and value <= kill_switch_threshold:
                    kill_switch_hit = True
                    survival_steps.append(step)
                    break

            if ruin_hit:
                ruin_count += 1

            if kill_switch_hit:
                kill_switch_count += 1

            if not ruin_hit and not kill_switch_hit:
                survival_steps.append(len(path))

        total_paths = len(equity_paths)

        ruin_probability = ruin_count / total_paths
        kill_switch_probability = kill_switch_count / total_paths
        survival_probability = 1.0 - ruin_probability

        expected_survival_horizon = sum(survival_steps) / len(survival_steps)

        return {
            "ruin_probability": ruin_probability,
            "kill_switch_probability": kill_switch_probability,
            "survival_probability": survival_probability,
            "expected_survival_horizon": expected_survival_horizon,
            "ruin_paths": ruin_count,
            "total_paths": total_paths,
        }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "model": "ForwardRuinProbability",
            "version": self.VERSION,
        }