from __future__ import annotations

import threading
import time
from typing import List, Dict, Any, Optional, Union

from visualization.charts.base_chart import BaseChart, BaseChartError


Number = Union[int, float]


class PieChart(BaseChart):
    """
    Institutional Pie Chart

    Used For
    --------
    • Capital allocation
    • Portfolio exposure
    • Risk contribution
    • Trade distribution
    • Strategy allocation

    Design Goals
    ------------
    • Deterministic output
    • Thread-safe
    • Non-blocking
    • Replay-safe
    """

    MAX_SLICES = 10000

    def __init__(
        self,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):
        super().__init__(
            chart_type="pie",
            title=title,
            monitoring_registry=monitoring_registry,
        )

        self._labels: List[str] = []
        self._values: List[Number] = []
        self._colors: List[Optional[str]] = []
        self._metadata: List[Dict[str, Any]] = []

        self._data_lock = threading.Lock()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def _validate_labels(self, labels: List[str]) -> None:

        if not isinstance(labels, list):
            raise BaseChartError("labels must be list")

        if len(labels) == 0:
            raise BaseChartError("labels cannot be empty")

        if len(labels) > self.MAX_SLICES:
            raise BaseChartError("too many pie slices")

    def _validate_values(self, values: List[Number]) -> None:

        if not isinstance(values, list):
            raise BaseChartError("values must be list")

        for v in values:
            if not isinstance(v, (int, float)):
                raise BaseChartError("pie values must be numeric")

    # -------------------------------------------------
    # Data Setup
    # -------------------------------------------------

    def set_slices(
        self,
        labels: List[str],
        values: List[Number],
        colors: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Set pie slices.

        Example
        -------
        Capital allocation
        Portfolio exposure
        """

        self._validate_labels(labels)
        self._validate_values(values)

        if len(labels) != len(values):
            raise BaseChartError("labels and values length mismatch")

        if colors and len(colors) != len(labels):
            raise BaseChartError("colors length mismatch")

        if metadata and len(metadata) != len(labels):
            raise BaseChartError("metadata length mismatch")

        with self._data_lock:

            self._labels = list(labels)
            self._values = list(values)
            self._colors = list(colors) if colors else [None] * len(labels)
            self._metadata = list(metadata) if metadata else [{}] * len(labels)

    # -------------------------------------------------
    # Update Slice
    # -------------------------------------------------

    def update_slice(
        self,
        label_index: int,
        value: Number,
    ) -> None:

        with self._data_lock:

            if label_index >= len(self._values):
                raise BaseChartError("slice index out of range")

            if not isinstance(value, (int, float)):
                raise BaseChartError("value must be numeric")

            self._values[label_index] = value

    # -------------------------------------------------
    # Layout
    # -------------------------------------------------

    def configure_layout(
        self,
        show_percentage: bool = True,
        donut: bool = False,
    ) -> None:

        self.set_layout(
            {
                "show_percentage": show_percentage,
                "donut": donut,
            }
        )

    # -------------------------------------------------
    # Data Build
    # -------------------------------------------------

    def _build_data(self) -> Dict[str, Any]:

        with self._data_lock:

            slices = []

            for i in range(len(self._labels)):

                slices.append(
                    {
                        "label": self._labels[i],
                        "value": self._values[i],
                        "color": self._colors[i],
                        "metadata": self._metadata[i],
                    }
                )

            return {"slices": slices}

    # -------------------------------------------------
    # Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            self.set_data(self._build_data())

            return super().export()

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "chart_id": self.chart_id,
            "chart_type": "pie",
            "slice_count": len(self._labels),
            "timestamp": time.time(),
        }