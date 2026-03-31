from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class CapitalTraceError(Exception):
    pass


class CapitalTrace:
    """
    Institutional Capital Trace Logger

    Responsibilities
    ----------------
    • Record all capital allocation decisions
    • Track position sizing changes
    • Record Kelly and risk budgeting outputs
    • Preserve capital governance history
    • Remain deterministic and thread-safe
    """

    VERSION = 1
    MAX_TRACES = 10000

    def __init__(self):

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Record Capital Decision
    # -------------------------------------------------

    def record_capital_event(
        self,
        component: str,
        event_type: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not component:
            raise CapitalTraceError("component required")

        if not event_type:
            raise CapitalTraceError("event_type required")

        trace_id = str(uuid.uuid4())

        trace = {
            "trace_id": trace_id,
            "component": component,
            "event_type": event_type,
            "inputs": inputs or {},
            "outputs": outputs or {},
            "constraints": constraints or {},
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        with self._lock:

            self._traces.append(trace)

            if len(self._traces) > self.MAX_TRACES:
                self._traces.pop(0)

        return trace_id

    # -------------------------------------------------
    # Query Trace
    # -------------------------------------------------

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:

        with self._lock:

            for trace in self._traces:
                if trace["trace_id"] == trace_id:
                    return dict(trace)

        return None

    # -------------------------------------------------
    # Component Queries
    # -------------------------------------------------

    def get_component_events(
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
    # Event Type Queries
    # -------------------------------------------------

    def get_event_type(
        self,
        event_type: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t["event_type"] == event_type
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Statistics
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
            "total_capital_events": total,
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