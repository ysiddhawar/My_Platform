from __future__ import annotations

import uuid
import time
import threading
from typing import Dict, Any, Optional


class BaseChartError(Exception):
    pass


class BaseChart:
    """
    Institutional Base Chart

    Responsibilities
    ----------------
    • Provide standardized chart structure
    • Validate chart data
    • Ensure serialization safety
    • Provide deterministic chart metadata
    • Remain thread-safe and non-blocking
    """

    VERSION = 1

    def __init__(
        self,
        chart_type: str,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):

        if not chart_type:
            raise BaseChartError("chart_type required")

        if not title:
            raise BaseChartError("title required")

        self.chart_id = str(uuid.uuid4())
        self.chart_type = chart_type
        self.title = title

        self._data: Dict[str, Any] = {}
        self._layout: Dict[str, Any] = {}

        self._metadata = {
            "created_at": time.time(),
            "version": self.VERSION,
        }

        self._monitoring_registry = monitoring_registry

        self._lock = threading.Lock()

    # -------------------------------------------------
    # Data Handling
    # -------------------------------------------------

    def set_data(self, data: Dict[str, Any]) -> None:

        if not isinstance(data, dict):
            raise BaseChartError("chart data must be dict")

        with self._lock:
            self._data = data

    def get_data(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)

    # -------------------------------------------------
    # Layout Handling
    # -------------------------------------------------

    def set_layout(self, layout: Dict[str, Any]) -> None:

        if not isinstance(layout, dict):
            raise BaseChartError("layout must be dict")

        with self._lock:
            self._layout = layout

    def get_layout(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._layout)

    # -------------------------------------------------
    # Metadata
    # -------------------------------------------------

    def set_metadata(self, key: str, value: Any) -> None:

        if not key:
            raise BaseChartError("metadata key required")

        with self._lock:
            self._metadata[key] = value

    def get_metadata(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metadata)

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def validate(self) -> None:

        if not isinstance(self._data, dict):
            raise BaseChartError("chart data invalid")

        if not isinstance(self._layout, dict):
            raise BaseChartError("chart layout invalid")

    # -------------------------------------------------
    # Chart Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            self.validate()

            return {
                "chart_id": self.chart_id,
                "type": self.chart_type,
                "title": self.title,
                "data": dict(self._data),
                "layout": dict(self._layout),
                "metadata": dict(self._metadata),
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type,
            "version": self.VERSION,
        }