from __future__ import annotations

import threading
from typing import Dict, Any, List, Optional, Tuple


class ForwardDrawdownEstimatorError(Exception):
    pass


class ForwardDrawdownEstimator:
    """
    Institutional Forward Drawdown Estimator

    Responsibilities
    ----------------
    • Estimate expected future drawdown
    • Estimate worst-case drawdown
    • Estimate drawdown duration
    • Estimate tail drawdown risk
    • Remain deterministic and thread-safe
    """

    VERSION = 1

    DEFAULT_CONFIDENCE_LEVEL = 0.95

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
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    ) -> Dict[str, Any]:

        if not equity_paths:
            raise ForwardDrawdownEstimatorError("equity_paths required")

        drawdowns: List[float] = []
        durations: List[int] = []

        for path in equity_paths:

            dd, dur = self._path_drawdown_stats(path)

            drawdowns.append(dd)
            durations.append(dur)

        expected_drawdown = sum(drawdowns) / len(drawdowns)

        worst_case_drawdown = max(drawdowns)

        tail_drawdown = self._percentile(drawdowns, confidence_level)

        expected_duration = sum(durations) / len(durations)

        return {
            "expected_drawdown": expected_drawdown,
            "worst_case_drawdown": worst_case_drawdown,
            "tail_drawdown": tail_drawdown,
            "expected_drawdown_duration": expected_duration,
            "drawdown_distribution": drawdowns,
        }

    # -------------------------------------------------
    # Drawdown Stats for Single Path
    # -------------------------------------------------

    def _path_drawdown_stats(
        self,
        path: List[float]
    ) -> Tuple[float, int]:

        peak = path[0]
        max_drawdown = 0.0

        duration = 0
        max_duration = 0

        for value in path:

            if value > peak:
                peak = value
                duration = 0
            else:

                drawdown = (peak - value) / peak

                duration += 1

                if drawdown > max_drawdown:
                    max_drawdown = drawdown

                if duration > max_duration:
                    max_duration = duration

        return max_drawdown, max_duration

    # -------------------------------------------------
    # Percentile Utility
    # -------------------------------------------------

    def _percentile(
        self,
        values: List[float],
        p: float
    ) -> float:

        if not values:
            return 0.0

        sorted_vals = sorted(values)

        index = int(p * len(sorted_vals))

        index = min(index, len(sorted_vals) - 1)

        return sorted_vals[index]

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "model": "ForwardDrawdownEstimator",
            "version": self.VERSION,
        }