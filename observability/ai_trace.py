from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class AITraceError(Exception):
    pass


class AITrace:
    """
    Institutional AI Trace Logger

    Responsibilities
    ----------------
    • Record AI reasoning pipeline
    • Track metric interpretation outputs
    • Record weakness detection
    • Record behavioral analysis
    • Record AI prescriptions
    • Remain deterministic and thread-safe
    """

    VERSION = 1
    MAX_TRACES = 10000

    def __init__(self):

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Record AI Step
    # -------------------------------------------------

    def record_step(
        self,
        component: str,
        stage: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not component:
            raise AITraceError("component required")

        if not stage:
            raise AITraceError("stage required")

        trace_id = str(uuid.uuid4())

        trace = {
            "trace_id": trace_id,
            "component": component,
            "stage": stage,
            "inputs": inputs or {},
            "outputs": outputs or {},
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
    # Component Traces
    # -------------------------------------------------

    def get_component_traces(
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
    # Stage Traces
    # -------------------------------------------------

    def get_stage_traces(
        self,
        stage: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t["stage"] == stage
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Statistics
    # -------------------------------------------------

    def stats(self) -> Dict[str, Any]:

        with self._lock:

            total = len(self._traces)

            stage_counts: Dict[str, int] = {}

            for trace in self._traces:

                stage = trace["stage"]

                stage_counts[stage] = (
                    stage_counts.get(stage, 0) + 1
                )

        return {
            "total_ai_traces": total,
            "stages": stage_counts,
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