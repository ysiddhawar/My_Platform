from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class ExecutionTraceError(Exception):
    pass


class ExecutionTrace:
    """
    Institutional Execution Trace Logger

    Responsibilities
    ----------------
    • Record all execution layer events
    • Track order lifecycle
    • Record execution guard blocks
    • Preserve broker interaction history
    • Remain deterministic and thread-safe
    """

    VERSION = 1
    MAX_TRACES = 10000

    def __init__(self):

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Record Execution Event
    # -------------------------------------------------

    def record_execution_event(
        self,
        component: str,
        event_type: str,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not component:
            raise ExecutionTraceError("component required")

        if not event_type:
            raise ExecutionTraceError("event_type required")

        trace_id = str(uuid.uuid4())

        trace = {
            "trace_id": trace_id,
            "component": component,
            "event_type": event_type,
            "order_id": order_id,
            "symbol": symbol,
            "inputs": inputs or {},
            "outcome": outcome or {},
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
    # Order History
    # -------------------------------------------------

    def get_order_history(
        self,
        order_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t.get("order_id") == order_id
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Symbol History
    # -------------------------------------------------

    def get_symbol_events(
        self,
        symbol: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t.get("symbol") == symbol
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Component Events
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
    # Statistics
    # -------------------------------------------------

    def stats(self) -> Dict[str, Any]:

        with self._lock:

            total = len(self._traces)

            event_counts: Dict[str, int] = {}

            for trace in self._traces:

                event = trace["event_type"]

                event_counts[event] = (
                    event_counts.get(event, 0) + 1
                )

        return {
            "total_execution_events": total,
            "event_types": event_counts,
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