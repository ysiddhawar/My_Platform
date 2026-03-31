from __future__ import annotations

import time
import threading
from typing import Dict, Any, List, Optional


class MonitoringRegistryError(Exception):
    pass


class MonitoringRegistry:
    """
    Central Monitoring Event Registry

    Responsibilities
    ----------------
    • Collect monitoring events from all monitoring modules
    • Store anomalies, guard events, latency and metric runtime records
    • Provide monitoring snapshots for dashboards and diagnostics
    • Remain thread-safe and non-blocking
    """

    VERSION = 1

    MAX_EVENTS = 5000

    def __init__(self):

        self._anomalies: List[Dict[str, Any]] = []
        self._guard_events: List[Dict[str, Any]] = []
        self._latency_records: List[Dict[str, Any]] = []
        self._metric_runtime_records: List[Dict[str, Any]] = []
        self._health_events: List[Dict[str, Any]] = []

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Anomaly Recording
    # -------------------------------------------------

    def record_anomaly(self, anomaly: Dict[str, Any]) -> None:

        if not anomaly:
            return

        anomaly["timestamp"] = anomaly.get("timestamp", time.time())

        with self._lock:

            self._anomalies.append(anomaly)

            if len(self._anomalies) > self.MAX_EVENTS:
                self._anomalies.pop(0)

    # -------------------------------------------------
    # Guard Event Recording
    # -------------------------------------------------

    def record_guard_event(self, event: Dict[str, Any]) -> None:

        if not event:
            return

        event["timestamp"] = event.get("timestamp", time.time())

        with self._lock:

            self._guard_events.append(event)

            if len(self._guard_events) > self.MAX_EVENTS:
                self._guard_events.pop(0)

    # -------------------------------------------------
    # Latency Recording
    # -------------------------------------------------

    def record_latency(self, component: str, latency: float) -> None:

        if latency < 0:
            return

        record = {
            "component": component,
            "latency": latency,
            "timestamp": time.time()
        }

        with self._lock:

            self._latency_records.append(record)

            if len(self._latency_records) > self.MAX_EVENTS:
                self._latency_records.pop(0)

    # -------------------------------------------------
    # Metric Runtime Recording
    # -------------------------------------------------

    def record_metric_runtime(self, metric: str, runtime: float) -> None:

        if runtime < 0:
            return

        record = {
            "metric": metric,
            "runtime": runtime,
            "timestamp": time.time()
        }

        with self._lock:

            self._metric_runtime_records.append(record)

            if len(self._metric_runtime_records) > self.MAX_EVENTS:
                self._metric_runtime_records.pop(0)

    # -------------------------------------------------
    # Health Event Recording
    # -------------------------------------------------

    def record_health_event(self, event: Dict[str, Any]) -> None:

        if not event:
            return

        event["timestamp"] = event.get("timestamp", time.time())

        with self._lock:

            self._health_events.append(event)

            if len(self._health_events) > self.MAX_EVENTS:
                self._health_events.pop(0)

    # -------------------------------------------------
    # Query Methods
    # -------------------------------------------------

    def get_recent_anomalies(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._anomalies[-limit:])

    def get_recent_guard_events(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._guard_events[-limit:])

    def get_recent_latency(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._latency_records[-limit:])

    def get_recent_metric_runtime(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._metric_runtime_records[-limit:])

    def get_recent_health_events(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._health_events[-limit:])

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "anomaly_count": len(self._anomalies),
                "guard_event_count": len(self._guard_events),
                "latency_records": len(self._latency_records),
                "metric_runtime_records": len(self._metric_runtime_records),
                "health_events": len(self._health_events),
                "timestamp": time.time()
            }

    # -------------------------------------------------
    # Reset
    # -------------------------------------------------

    def reset(self) -> None:

        with self._lock:

            self._anomalies.clear()
            self._guard_events.clear()
            self._latency_records.clear()
            self._metric_runtime_records.clear()
            self._health_events.clear()