from __future__ import annotations

import time
import threading
from typing import Dict, Any, Optional, List
from collections import deque


class GuardMonitorError(Exception):
    pass


class GuardMonitor:
    """
    Institutional Guard Monitor

    Responsibilities
    ----------------
    • Observe risk guards and discipline gates
    • Record guard trigger events
    • Detect excessive guard activation
    • Provide runtime guard analytics
    • Remain deterministic and thread-safe
    • Never interfere with execution pipeline
    """

    VERSION = 1

    DEFAULT_WINDOW = 200
    GUARD_SPIKE_THRESHOLD = 10

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None,
        window_size: int = DEFAULT_WINDOW,
    ):

        if window_size <= 0:
            raise GuardMonitorError("window_size must be positive")

        self._registry = monitoring_registry
        self._window_size = window_size

        self._guard_windows: Dict[str, deque] = {}
        self._guard_history: List[Dict[str, Any]] = []

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Guard Trigger Recording
    # -------------------------------------------------

    def record_guard_trigger(
        self,
        guard_name: str,
        component: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:

        if not guard_name:
            raise GuardMonitorError("guard_name required")

        now = time.time()

        event = {
            "guard": guard_name,
            "component": component,
            "context": context or {},
            "timestamp": now,
        }

        with self._lock:

            window = self._guard_windows.setdefault(
                guard_name,
                deque(maxlen=self._window_size),
            )

            window.append(now)

            self._guard_history.append(event)

            if len(self._guard_history) > 5000:
                self._guard_history.pop(0)

            recent = [t for t in window if now - t < 60]

            if len(recent) >= self.GUARD_SPIKE_THRESHOLD:

                anomaly = {
                    "type": "guard_activation_spike",
                    "guard": guard_name,
                    "count_last_minute": len(recent),
                    "timestamp": now,
                }

                self._emit(anomaly)

                return anomaly

        if self._registry:
            self._registry.record_guard_event(event)

        return None

    # -------------------------------------------------
    # Guard Statistics
    # -------------------------------------------------

    def get_guard_stats(self, guard_name: str) -> Dict[str, Any]:

        with self._lock:

            window = self._guard_windows.get(guard_name)

            if not window:
                return {}

            timestamps = list(window)

        count = len(timestamps)

        return {
            "guard": guard_name,
            "activation_count": count,
            "last_activation": timestamps[-1] if timestamps else None,
        }

    # -------------------------------------------------
    # Guard History
    # -------------------------------------------------

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._guard_history[-limit:])

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            guards = list(self._guard_windows.keys())

        stats = {}

        for guard in guards:
            stats[guard] = self.get_guard_stats(guard)

        return {
            "guards_monitored": len(stats),
            "guard_stats": stats,
            "timestamp": time.time(),
        }

    # -------------------------------------------------
    # Emit Anomaly
    # -------------------------------------------------

    def _emit(self, anomaly: Dict[str, Any]) -> None:

        if self._registry:
            self._registry.record_anomaly(anomaly)