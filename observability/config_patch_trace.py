from __future__ import annotations

import time
import threading
import uuid
from typing import Dict, Any, List, Optional


class ConfigPatchTraceError(Exception):
    pass


class ConfigPatchTrace:
    """
    Institutional Configuration Patch Trace Logger

    Responsibilities
    ----------------
    • Record all configuration updates
    • Track AI-recommended configuration patches
    • Preserve before/after configuration state
    • Support governance auditing and replay verification
    • Remain deterministic and thread-safe
    """

    VERSION = 1
    MAX_TRACES = 10000

    def __init__(self):

        self._traces: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # -------------------------------------------------
    # Record Patch
    # -------------------------------------------------

    def record_patch(
        self,
        component: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
        source: str = "ai",
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not component:
            raise ConfigPatchTraceError("component required")

        if not parameter:
            raise ConfigPatchTraceError("parameter required")

        patch_id = str(uuid.uuid4())

        trace = {
            "patch_id": patch_id,
            "component": component,
            "parameter": parameter,
            "old_value": old_value,
            "new_value": new_value,
            "source": source,  # ai | user | governance
            "reasoning": reasoning,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        with self._lock:

            self._traces.append(trace)

            if len(self._traces) > self.MAX_TRACES:
                self._traces.pop(0)

        return patch_id

    # -------------------------------------------------
    # Query Patch
    # -------------------------------------------------

    def get_patch(self, patch_id: str) -> Optional[Dict[str, Any]]:

        with self._lock:

            for trace in self._traces:
                if trace["patch_id"] == patch_id:
                    return dict(trace)

        return None

    # -------------------------------------------------
    # Component Patch History
    # -------------------------------------------------

    def get_component_patches(
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
    # Parameter Patch History
    # -------------------------------------------------

    def get_parameter_history(
        self,
        parameter: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:

        with self._lock:

            results = [
                t for t in self._traces
                if t["parameter"] == parameter
            ]

        return results[-limit:]

    # -------------------------------------------------
    # Statistics
    # -------------------------------------------------

    def stats(self) -> Dict[str, Any]:

        with self._lock:

            total = len(self._traces)

            parameter_counts: Dict[str, int] = {}

            for trace in self._traces:

                parameter = trace["parameter"]

                parameter_counts[parameter] = (
                    parameter_counts.get(parameter, 0) + 1
                )

        return {
            "total_config_patches": total,
            "parameters_modified": parameter_counts,
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