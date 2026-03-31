from __future__ import annotations

import time
import threading
from typing import Dict, Any, Optional, List
from collections import deque


class AnomalyDetectorError(Exception):
    pass


class AnomalyDetector:
    """
    Institutional Runtime Anomaly Detector

    Responsibilities
    ----------------
    • Detect runtime anomalies across platform components
    • Monitor latency drift
    • Monitor error bursts
    • Detect abnormal metric outputs
    • Detect execution instability signals
    • Remain deterministic and thread-safe
    • Never interfere with execution pipeline
    """

    VERSION = 1

    DEFAULT_WINDOW = 200
    LATENCY_SPIKE_FACTOR = 3.0
    ERROR_BURST_THRESHOLD = 5

    def __init__(
        self,
        latency_tracker: Optional[Any] = None,
        monitoring_registry: Optional[Any] = None,
        window_size: int = DEFAULT_WINDOW
    ):

        if window_size <= 0:
            raise AnomalyDetectorError("window_size must be positive")

        self._latency_tracker = latency_tracker
        self._registry = monitoring_registry

        self._window_size = window_size

        self._metric_windows: Dict[str, deque] = {}
        self._error_windows: Dict[str, deque] = {}

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Metric Monitoring
    # -------------------------------------------------

    def record_metric(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:

        if not metric_name:
            raise AnomalyDetectorError("metric_name required")

        with self._lock:

            window = self._metric_windows.setdefault(
                metric_name,
                deque(maxlen=self._window_size)
            )

            window.append(value)

            if len(window) < 10:
                return None

            mean = sum(window) / len(window)

            deviation = abs(value - mean)

            if mean != 0:
                ratio = deviation / abs(mean)
            else:
                ratio = 0

            if ratio > 3:

                anomaly = {
                    "type": "metric_spike",
                    "metric": metric_name,
                    "value": value,
                    "mean": mean,
                    "timestamp": time.time()
                }

                self._emit(anomaly)

                return anomaly

        return None

    # -------------------------------------------------
    # Latency Anomaly
    # -------------------------------------------------

    def detect_latency_anomaly(self, component: str) -> Optional[Dict[str, Any]]:

        if not self._latency_tracker:
            return None

        stats = self._latency_tracker.get_stats(component)

        if not stats:
            return None

        mean_latency = stats["mean_latency"]
        p99_latency = stats["p99_latency"]

        if mean_latency <= 0:
            return None

        ratio = p99_latency / mean_latency

        if ratio > self.LATENCY_SPIKE_FACTOR:

            anomaly = {
                "type": "latency_spike",
                "component": component,
                "mean_latency": mean_latency,
                "p99_latency": p99_latency,
                "timestamp": time.time()
            }

            self._emit(anomaly)

            return anomaly

        return None

    # -------------------------------------------------
    # Error Burst Detection
    # -------------------------------------------------

    def record_error(self, component: str, error: Exception) -> Optional[Dict[str, Any]]:

        now = time.time()

        with self._lock:

            window = self._error_windows.setdefault(
                component,
                deque(maxlen=self._window_size)
            )

            window.append(now)

            recent_errors = [
                t for t in window if now - t < 10
            ]

            if len(recent_errors) >= self.ERROR_BURST_THRESHOLD:

                anomaly = {
                    "type": "error_burst",
                    "component": component,
                    "error_count": len(recent_errors),
                    "timestamp": now
                }

                self._emit(anomaly)

                return anomaly

        return None

    # -------------------------------------------------
    # Execution Instability Detection
    # -------------------------------------------------

    def detect_execution_instability(
        self,
        execution_metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        if not execution_metrics:
            return None

        spread = execution_metrics.get("spread")
        slippage = execution_metrics.get("slippage")

        if spread is None or slippage is None:
            return None

        if spread > 5 * slippage:

            anomaly = {
                "type": "execution_instability",
                "spread": spread,
                "slippage": slippage,
                "timestamp": time.time()
            }

            self._emit(anomaly)

            return anomaly

        return None

    # -------------------------------------------------
    # Emit Anomaly
    # -------------------------------------------------

    def _emit(self, anomaly: Dict[str, Any]) -> None:

        if self._registry:
            self._registry.record_anomaly(anomaly)

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "metric_windows": len(self._metric_windows),
                "error_windows": len(self._error_windows),
                "timestamp": time.time(),
            }