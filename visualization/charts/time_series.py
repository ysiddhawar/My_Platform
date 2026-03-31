from __future__ import annotations

import threading
import time
from typing import List, Dict, Any, Optional, Union

from visualization.charts.base_chart import BaseChart, BaseChartError


Number = Union[int, float]


class TimeSeriesChart(BaseChart):
    """
    Institutional Time Series Chart

    Used For
    --------
    • Equity curves
    • Rolling Sharpe
    • Rolling volatility
    • Drawdown curves
    • Portfolio value
    • Capital curves
    • Strategy comparison

    Design Goals
    ------------
    • Deterministic chart output
    • Thread-safe
    • Non-blocking
    • Replay-safe
    • Monitoring compatible
    """

    MAX_POINTS = 1_000_000  # Safety guard

    def __init__(
        self,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):
        super().__init__(
            chart_type="time_series",
            title=title,
            monitoring_registry=monitoring_registry,
        )

        self._series: Dict[str, Dict[str, List[Any]]] = {}
        self._series_lock = threading.Lock()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def _validate_series(
        self,
        x: List[Any],
        y: List[Number],
    ) -> None:

        if not isinstance(x, list):
            raise BaseChartError("time_series x must be list")

        if not isinstance(y, list):
            raise BaseChartError("time_series y must be list")

        if len(x) != len(y):
            raise BaseChartError("x and y length mismatch")

        if len(x) == 0:
            raise BaseChartError("time_series cannot be empty")

        if len(x) > self.MAX_POINTS:
            raise BaseChartError("time_series exceeds max points")

    # -------------------------------------------------
    # Series Management
    # -------------------------------------------------

    def add_series(
        self,
        name: str,
        x: List[Any],
        y: List[Number],
        color: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a time series to chart.

        Example
        -------
        equity curve
        rolling sharpe
        drawdown curve
        """

        if not name:
            raise BaseChartError("series name required")

        self._validate_series(x, y)

        with self._series_lock:

            self._series[name] = {
                "x": list(x),
                "y": list(y),
                "color": color,
                "metadata": metadata or {},
            }

    # -------------------------------------------------
    # Append Point (Streaming Safe)
    # -------------------------------------------------

    def append_point(
        self,
        name: str,
        x: Any,
        y: Number,
    ) -> None:
        """
        Append point safely.

        Used for live updates.
        """

        with self._series_lock:

            if name not in self._series:
                raise BaseChartError(f"series '{name}' not found")

            series = self._series[name]

            series["x"].append(x)
            series["y"].append(y)

            if len(series["x"]) > self.MAX_POINTS:
                series["x"].pop(0)
                series["y"].pop(0)

    # -------------------------------------------------
    # Layout Helpers
    # -------------------------------------------------

    def configure_axes(
        self,
        x_label: str,
        y_label: str,
        x_type: str = "time",
        y_type: str = "linear",
    ) -> None:

        self.set_layout(
            {
                "x_label": x_label,
                "y_label": y_label,
                "x_type": x_type,
                "y_type": y_type,
            }
        )

    # -------------------------------------------------
    # Data Build
    # -------------------------------------------------

    def _build_data(self) -> Dict[str, Any]:

        with self._series_lock:

            output = []

            for name, series in self._series.items():

                output.append(
                    {
                        "name": name,
                        "x": list(series["x"]),
                        "y": list(series["y"]),
                        "color": series.get("color"),
                        "metadata": series.get("metadata", {}),
                    }
                )

            return {"series": output}

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
            "chart_type": "time_series",
            "series_count": len(self._series),
            "timestamp": time.time(),
        }