from __future__ import annotations

import threading
import time
from typing import List, Dict, Any, Optional, Union

from visualization.charts.base_chart import BaseChart, BaseChartError


Number = Union[int, float]


class BarChart(BaseChart):
    """
    Institutional Bar Chart

    Used For
    --------
    • Strategy comparison
    • Symbol performance
    • Discipline score breakdown
    • Risk contribution
    • Capital allocation
    • AI improvement metrics

    Design Goals
    ------------
    • Deterministic output
    • Thread-safe
    • Non-blocking
    • Replay-safe
    """

    MAX_BARS = 10000

    def __init__(
        self,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):
        super().__init__(
            chart_type="bar",
            title=title,
            monitoring_registry=monitoring_registry,
        )

        self._categories: List[str] = []
        self._series: Dict[str, Dict[str, Any]] = {}

        self._data_lock = threading.Lock()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def _validate_categories(
        self,
        categories: List[str],
    ) -> None:

        if not isinstance(categories, list):
            raise BaseChartError("categories must be list")

        if len(categories) == 0:
            raise BaseChartError("categories cannot be empty")

        if len(categories) > self.MAX_BARS:
            raise BaseChartError("too many bar categories")

    def _validate_values(
        self,
        values: List[Number],
    ) -> None:

        if not isinstance(values, list):
            raise BaseChartError("values must be list")

        for v in values:
            if not isinstance(v, (int, float)):
                raise BaseChartError("bar values must be numeric")

    # -------------------------------------------------
    # Categories
    # -------------------------------------------------

    def set_categories(
        self,
        categories: List[str],
    ) -> None:

        self._validate_categories(categories)

        with self._data_lock:
            self._categories = list(categories)

    # -------------------------------------------------
    # Series Management
    # -------------------------------------------------

    def add_series(
        self,
        name: str,
        values: List[Number],
        color: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add bar series.

        Example
        -------
        Strategy comparison
        Symbol profitability
        """

        if not name:
            raise BaseChartError("series name required")

        self._validate_values(values)

        with self._data_lock:

            if not self._categories:
                raise BaseChartError("set categories before adding series")

            if len(values) != len(self._categories):
                raise BaseChartError("values must match category count")

            self._series[name] = {
                "values": list(values),
                "color": color,
                "metadata": metadata or {},
            }

    # -------------------------------------------------
    # Update Value
    # -------------------------------------------------

    def update_value(
        self,
        series_name: str,
        category_index: int,
        value: Number,
    ) -> None:
        """
        Safely update a bar value.
        """

        with self._data_lock:

            if series_name not in self._series:
                raise BaseChartError("series not found")

            if category_index >= len(self._categories):
                raise BaseChartError("category index out of range")

            self._series[series_name]["values"][category_index] = value

    # -------------------------------------------------
    # Layout Helpers
    # -------------------------------------------------

    def configure_layout(
        self,
        x_label: str,
        y_label: str,
        orientation: str = "vertical",
    ) -> None:

        self.set_layout(
            {
                "x_label": x_label,
                "y_label": y_label,
                "orientation": orientation,
            }
        )

    # -------------------------------------------------
    # Data Build
    # -------------------------------------------------

    def _build_data(self) -> Dict[str, Any]:

        with self._data_lock:

            series_output = []

            for name, series in self._series.items():

                series_output.append(
                    {
                        "name": name,
                        "values": list(series["values"]),
                        "color": series.get("color"),
                        "metadata": series.get("metadata", {}),
                    }
                )

            return {
                "categories": list(self._categories),
                "series": series_output,
            }

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
            "chart_type": "bar",
            "categories": len(self._categories),
            "series_count": len(self._series),
            "timestamp": time.time(),
        }