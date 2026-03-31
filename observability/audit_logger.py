from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class AuditLoggerError(Exception):
    pass


class AuditLogger:
    """
    Institutional Audit Logger

    Responsibilities
    ----------------
    • Aggregate audit events across the entire platform
    • Provide replayable audit history
    • Preserve event ordering
    • Remain thread-safe and non-blocking
    """

    VERSION = 1
    MAX_LOGS = 20000

    def __init__(self):

        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Log Event
    # -------------------------------------------------

    def log_event(
        self,
        category: str,
        component: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not category:
            raise AuditLoggerError("category required")

        if not component:
            raise AuditLoggerError("component required")

        if not event_type:
            raise AuditLoggerError("event_type required")

        log_id = str(uuid.uuid4())

        log = {
            "log_id": log_id,
            "category": category,     # ai | execution | capital | config | monitoring
            "component": component,
            "event_type": event_type,
            "details": details or {},
            "severity": severity,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        with self._lock:

            self._logs.append(log)

            if len(self._logs) > self.MAX_LOGS:
                self._logs.pop(0)

        return log_id

    # -------------------------------------------------
    # Query Log
    # -------------------------------------------------

    def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:

        with self._lock:

            for log in self._logs:
                if log["log_id"] == log_id:
                    return dict(log)

        return None

    # -------------------------------------------------
    # Category Logs
    # -------------------------------------------------

    def get_category_logs(
        self,
        category: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                log for log in self._logs
                if log["category"] == category
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Component Logs
    # -------------------------------------------------

    def get_component_logs(
        self,
        component: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                log for log in self._logs
                if log["component"] == component
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Severity Logs
    # -------------------------------------------------

    def get_severity_logs(
        self,
        severity: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                log for log in self._logs
                if log["severity"] == severity
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Statistics
    # -------------------------------------------------

    def stats(self) -> Dict[str, Any]:

        with self._lock:

            total = len(self._logs)

            category_counts: Dict[str, int] = {}

            for log in self._logs:

                category = log["category"]

                category_counts[category] = (
                    category_counts.get(category, 0) + 1
                )

        return {
            "total_logs": total,
            "categories": category_counts,
            "timestamp": time.time(),
        }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "log_count": len(self._logs),
                "timestamp": time.time(),
            }

    # -------------------------------------------------
    # Reset
    # -------------------------------------------------

    def reset(self) -> None:

        with self._lock:
            self._logs.clear()