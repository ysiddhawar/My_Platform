from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class DecisionTraceError(Exception):
    pass


class DecisionTrace:
    """
    Institutional Decision Trace Logger

    Responsibilities
    ----------------
    • Record every decision made by the platform
    • Preserve decision context and reasoning
    • Support audit trails and replay analysis
    • Remain thread-safe and non-blocking
    """

    VERSION = 1
    MAX_TRACES = 10000

    def __init__(self):

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Record Decision
    # -------------------------------------------------

    def record_decision(
        self,
        component: str,
        decision_type: str,
        inputs: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not component:
            raise DecisionTraceError("component required")

        if not decision_type:
            raise DecisionTraceError("decision_type required")

        decision_id = str(uuid.uuid4())

        trace = {
            "decision_id": decision_id,
            "component": component,
            "decision_type": decision_type,
            "inputs": inputs or {},
            "constraints": constraints or {},
            "outcome": outcome or {},
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        with self._lock:

            self._traces.append(trace)

            if len(self._traces) > self.MAX_TRACES:
                self._traces.pop(0)

        return decision_id

    # -------------------------------------------------
    # Query Decision
    # -------------------------------------------------

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:

        with self._lock:

            for trace in self._traces:
                if trace["decision_id"] == decision_id:
                    return dict(trace)

        return None

    # -------------------------------------------------
    # Recent Decisions
    # -------------------------------------------------

    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:

        with self._lock:
            return list(self._traces[-limit:])

    # -------------------------------------------------
    # Component Decisions
    # -------------------------------------------------

    def get_component_decisions(
        self,
        component: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t["component"] == component
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Decision Statistics
    # -------------------------------------------------

    def stats(self) -> Dict[str, Any]:

        with self._lock:

            total = len(self._traces)

            component_counts: Dict[str, int] = {}

            for trace in self._traces:

                component = trace["component"]

                component_counts[component] = (
                    component_counts.get(component, 0) + 1
                )

        return {
            "total_decisions": total,
            "components": component_counts,
            "timestamp": time.time(),
        }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "trace_count": len(self._traces),
                "timestamp": time.time(),
            }

    # -------------------------------------------------
    # Reset
    # -------------------------------------------------

    def reset(self) -> None:

        with self._lock:
            self._traces.clear()