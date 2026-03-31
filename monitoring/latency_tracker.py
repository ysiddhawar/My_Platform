from __future__ import annotations

import time
import threading
from typing import Dict, Any, Optional, List
from collections import deque


class LatencyTrackerError(Exception):
    pass


class LatencyTracker:
    """
    Institutional Latency Tracker

    Responsibilities
    ----------------
    • Track latency across platform subsystems
    • Maintain sliding windows of latency metrics
    • Provide mean / max / percentile estimates
    • Remain non-blocking and thread-safe
    • Integrate with monitoring registry
    • Deterministic and replay safe
    """

    VERSION = 1

    DEFAULT_WINDOW_SIZE = 500

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None,
        window_size: int = DEFAULT_WINDOW_SIZE
    ):

        if window_size <= 0:
            raise LatencyTrackerError("window_size must be positive")

        self._registry = monitoring_registry
        self._window_size = window_size

        self._latency_windows: Dict[str, deque] = {}
        self._active_timers: Dict[str, float] = {}

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Timer Control
    # -------------------------------------------------

    def start_timer(self, component: str) -> None:

        if not component:
            raise LatencyTrackerError("component name required")

        now = time.perf_counter()

        with self._lock:
            self._active_timers[component] = now

    def stop_timer(self, component: str) -> float:

        now = time.perf_counter()

        with self._lock:

            start_time = self._active_timers.pop(component, None)

            if start_time is None:
                raise LatencyTrackerError(
                    f"No active timer for component: {component}"
                )

            latency = now - start_time

            window = self._latency_windows.setdefault(
                component,
                deque(maxlen=self._window_size)
            )

            window.append(latency)

        if self._registry:
            self._registry.record_latency(component, latency)

        return latency

    # -------------------------------------------------
    # Direct Recording
    # -------------------------------------------------

    def record_latency(self, component: str, latency: float) -> None:

        if latency < 0:
            raise LatencyTrackerError("latency cannot be negative")

        with self._lock:

            window = self._latency_windows.setdefault(
                component,
                deque(maxlen=self._window_size)
            )

            window.append(latency)

        if self._registry:
            self._registry.record_latency(component, latency)

    # -------------------------------------------------
    # Statistics
    # -------------------------------------------------

    def get_stats(self, component: str) -> Dict[str, Any]:

        with self._lock:

            window = self._latency_windows.get(component)

            if not window:
                return {}

            values: List[float] = list(window)

        values.sort()

        count = len(values)

        mean_latency = sum(values) / count
        max_latency = values[-1]
        min_latency = values[0]

        p95 = values[int(count * 0.95) - 1] if count > 1 else values[0]
        p99 = values[int(count * 0.99) - 1] if count > 1 else values[0]

        return {
            "component": component,
            "count": count,
            "mean_latency": mean_latency,
            "max_latency": max_latency,
            "min_latency": min_latency,
            "p95_latency": p95,
            "p99_latency": p99,
        }

    # -------------------------------------------------
    # Global Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Dict[str, Any]]:

        snapshot: Dict[str, Dict[str, Any]] = {}

        with self._lock:
            components = list(self._latency_windows.keys())

        for component in components:
            snapshot[component] = self.get_stats(component)

        return snapshot

    # -------------------------------------------------
    # Maintenance
    # -------------------------------------------------

    def reset_component(self, component: str) -> None:

        with self._lock:
            self._latency_windows.pop(component, None)

    def reset_all(self) -> None:

        with self._lock:
            self._latency_windows.clear()
            self._active_timers.clear()