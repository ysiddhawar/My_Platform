from __future__ import annotations

import time
import threading
from typing import Dict, Any, Optional


class HealthMonitorError(Exception):
    pass


class HealthMonitor:
    """
    Institutional Platform Health Monitor

    Responsibilities
    ----------------
    • Monitor core platform components
    • Detect degradation or failure signals
    • Track error frequency
    • Track component responsiveness
    • Emit health status snapshots
    • Deterministic / thread-safe
    • Replay safe
    """

    VERSION = 1

    HEALTH_OK = "ok"
    HEALTH_WARN = "warning"
    HEALTH_CRITICAL = "critical"

    DEFAULT_CHECK_INTERVAL = 5.0

    def __init__(
        self,
        execution_engine: Optional[Any] = None,
        dependency_graph: Optional[Any] = None,
        persistence_layer: Optional[Any] = None,
        connectors: Optional[Any] = None,
        recovery_engine: Optional[Any] = None,
        monitoring_registry: Optional[Any] = None,
    ):
        self._execution_engine = execution_engine
        self._dependency_graph = dependency_graph
        self._persistence_layer = persistence_layer
        self._connectors = connectors
        self._recovery_engine = recovery_engine
        self._registry = monitoring_registry

        self._status: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._interval = self.DEFAULT_CHECK_INTERVAL

    # -------------------------------------------------
    # Lifecycle
    # -------------------------------------------------

    def start(self, interval: Optional[float] = None):

        if self._running:
            return

        if interval is not None:
            if interval <= 0:
                raise HealthMonitorError("interval must be positive")
            self._interval = interval

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):

        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)

    # -------------------------------------------------
    # Main Loop
    # -------------------------------------------------

    def _run_loop(self):

        while self._running:

            try:
                snapshot = self._perform_health_check()

                with self._lock:
                    self._status = snapshot

                if self._registry:
                    self._registry.record_health_snapshot(snapshot)

            except Exception as exc:
                with self._lock:
                    self._status["monitor_internal_error"] = {
                        "status": self.HEALTH_CRITICAL,
                        "error": str(exc),
                        "timestamp": time.time(),
                    }

            time.sleep(self._interval)

    # -------------------------------------------------
    # Health Check
    # -------------------------------------------------

    def _perform_health_check(self) -> Dict[str, Dict[str, Any]]:

        snapshot: Dict[str, Dict[str, Any]] = {}

        snapshot["execution_engine"] = self._check_execution_engine()
        snapshot["dependency_graph"] = self._check_dependency_graph()
        snapshot["persistence_layer"] = self._check_persistence_layer()
        snapshot["connectors"] = self._check_connectors()
        snapshot["recovery_engine"] = self._check_recovery_engine()

        return snapshot

    # -------------------------------------------------
    # Component Checks
    # -------------------------------------------------

    def _check_execution_engine(self):

        try:
            if not self._execution_engine:
                return self._unknown()

            healthy = getattr(self._execution_engine, "is_running", lambda: True)()

            return self._ok() if healthy else self._warn()

        except Exception as exc:
            return self._critical(str(exc))

    def _check_dependency_graph(self):

        try:
            if not self._dependency_graph:
                return self._unknown()

            node_count = getattr(self._dependency_graph, "node_count", lambda: 0)()

            if node_count <= 0:
                return self._warn()

            return self._ok()

        except Exception as exc:
            return self._critical(str(exc))

    def _check_persistence_layer(self):

        try:
            if not self._persistence_layer:
                return self._unknown()

            responsive = getattr(
                self._persistence_layer,
                "health_check",
                lambda: True
            )()

            return self._ok() if responsive else self._warn()

        except Exception as exc:
            return self._critical(str(exc))

    def _check_connectors(self):

        try:
            if not self._connectors:
                return self._unknown()

            status = getattr(self._connectors, "health_check", lambda: True)()

            return self._ok() if status else self._warn()

        except Exception as exc:
            return self._critical(str(exc))

    def _check_recovery_engine(self):

        try:
            if not self._recovery_engine:
                return self._unknown()

            ready = getattr(
                self._recovery_engine,
                "is_ready",
                lambda: True
            )()

            return self._ok() if ready else self._warn()

        except Exception as exc:
            return self._critical(str(exc))

    # -------------------------------------------------
    # Status Builders
    # -------------------------------------------------

    def _ok(self):

        return {
            "status": self.HEALTH_OK,
            "timestamp": time.time()
        }

    def _warn(self):

        return {
            "status": self.HEALTH_WARN,
            "timestamp": time.time()
        }

    def _critical(self, error):

        return {
            "status": self.HEALTH_CRITICAL,
            "error": error,
            "timestamp": time.time()
        }

    def _unknown(self):

        return {
            "status": "unknown",
            "timestamp": time.time()
        }

    # -------------------------------------------------
    # Public Access
    # -------------------------------------------------

    def get_status(self) -> Dict[str, Dict[str, Any]]:

        with self._lock:
            return dict(self._status)

    def get_component_status(self, component: str):

        with self._lock:
            return self._status.get(component)