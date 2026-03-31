from __future__ import annotations

import time
import threading
from typing import Dict, Any, Optional, List
from collections import deque


class MetricsRuntimeTrackerError(Exception):
    pass


class MetricsRuntimeTracker:
    """
    Institutional Metrics Runtime Tracker

    Responsibilities
    ----------------
    • Track execution time of every metric
    • Detect slow metrics
    • Detect repeated metric failures
    • Provide runtime statistics for monitoring
    • Remain thread-safe and deterministic
    • Never interfere with metric execution
    """

    VERSION = 1

    DEFAULT_WINDOW = 200
    SLOW_METRIC_FACTOR = 3.0
    FAILURE_THRESHOLD = 5

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None,
        window_size: int = DEFAULT_WINDOW,
    ):

        if window_size <= 0:
            raise MetricsRuntimeTrackerError("window_size must be positive")

        self._registry = monitoring_registry
        self._window_size = window_size

        self._metric_windows: Dict[str, deque] = {}
        self._metric_failures: Dict[str, deque] = {}
        self._active_timers: Dict[str, float] = {}

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Metric Timer Control
    # -------------------------------------------------

    def start_metric(self, metric_name: str) -> None:

        if not metric_name:
            raise MetricsRuntimeTrackerError("metric_name required")

        now = time.perf_counter()

        with self._lock:
            self._active_timers[metric_name] = now

    def stop_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:

        now = time.perf_counter()

        with self._lock:

            start_time = self._active_timers.pop(metric_name, None)

            if start_time is None:
                return None

            runtime = now - start_time

            window = self._metric_windows.setdefault(
                metric_name,
                deque(maxlen=self._window_size)
            )

            window.append(runtime)

        if self._registry:
            self._registry.record_metric_runtime(metric_name, runtime)

        return self._detect_slow_metric(metric_name, runtime)

    # -------------------------------------------------
    # Failure Tracking
    # -------------------------------------------------

    def record_failure(self, metric_name: str, error: Exception) -> Optional[Dict[str, Any]]:

        now = time.time()

        with self._lock:

            window = self._metric_failures.setdefault(
                metric_name,
                deque(maxlen=self._window_size)
            )

            window.append(now)

            recent = [t for t in window if now - t < 60]

            if len(recent) >= self.FAILURE_THRESHOLD:

                anomaly = {
                    "type": "metric_failure_burst",
                    "metric": metric_name,
                    "failure_count": len(recent),
                    "timestamp": now
                }

                self._emit(anomaly)

                return anomaly

        return None

    # -------------------------------------------------
    # Slow Metric Detection
    # -------------------------------------------------

    def _detect_slow_metric(
        self,
        metric_name: str,
        runtime: float
    ) -> Optional[Dict[str, Any]]:

        with self._lock:

            window = self._metric_windows.get(metric_name)

            if not window or len(window) < 10:
                return None

            mean_runtime = sum(window) / len(window)

        if mean_runtime <= 0:
            return None

        ratio = runtime / mean_runtime

        if ratio > self.SLOW_METRIC_FACTOR:

            anomaly = {
                "type": "slow_metric",
                "metric": metric_name,
                "runtime": runtime,
                "mean_runtime": mean_runtime,
                "timestamp": time.time()
            }

            self._emit(anomaly)

            return anomaly

        return None

    # -------------------------------------------------
    # Metric Statistics
    # -------------------------------------------------

    def get_metric_stats(self, metric_name: str) -> Dict[str, Any]:

        with self._lock:

            window = self._metric_windows.get(metric_name)

            if not window:
                return {}

            values = list(window)

        values.sort()

        count = len(values)

        mean_runtime = sum(values) / count
        max_runtime = values[-1]
        min_runtime = values[0]

        p95 = values[int(count * 0.95) - 1] if count > 1 else values[0]
        p99 = values[int(count * 0.99) - 1] if count > 1 else values[0]

        return {
            "metric": metric_name,
            "count": count,
            "mean_runtime": mean_runtime,
            "max_runtime": max_runtime,
            "min_runtime": min_runtime,
            "p95_runtime": p95,
            "p99_runtime": p99,
        }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        stats = {}

        with self._lock:
            metrics = list(self._metric_windows.keys())

        for metric in metrics:
            stats[metric] = self.get_metric_stats(metric)

        return {
            "metrics_tracked": len(stats),
            "metrics": stats,
            "timestamp": time.time(),
        }

    # -------------------------------------------------
    # Emit Anomaly
    # -------------------------------------------------

    def _emit(self, anomaly: Dict[str, Any]) -> None:

        if self._registry:
            self._registry.record_anomaly(anomaly)