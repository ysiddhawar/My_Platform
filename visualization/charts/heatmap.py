from __future__ import annotations

import threading
import time
from typing import List, Dict, Any, Optional, Union

from visualization.charts.base_chart import BaseChart, BaseChartError


Number = Union[int, float]


class HeatmapChart(BaseChart):
    """
    Institutional Heatmap Chart

    Used For
    --------
    • Day-of-week PnL heatmap
    • Hour-of-day trading performance
    • Regime vs performance
    • Discipline violations heatmap
    • Strategy vs regime heatmap
    • Symbol profitability heatmap

    Design Goals
    ------------
    • Deterministic output
    • Thread-safe
    • Non-blocking
    • Replay-safe
    """

    MAX_ROWS = 1000
    MAX_COLS = 1000

    def __init__(
        self,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):
        super().__init__(
            chart_type="heatmap",
            title=title,
            monitoring_registry=monitoring_registry,
        )

        self._rows: List[str] = []
        self._cols: List[str] = []
        self._matrix: List[List[Number]] = []

        self._data_lock = threading.Lock()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def _validate_matrix(
        self,
        rows: List[str],
        cols: List[str],
        matrix: List[List[Number]],
    ) -> None:

        if not isinstance(rows, list):
            raise BaseChartError("rows must be list")

        if not isinstance(cols, list):
            raise BaseChartError("cols must be list")

        if not isinstance(matrix, list):
            raise BaseChartError("matrix must be list")

        if len(rows) == 0:
            raise BaseChartError("rows cannot be empty")

        if len(cols) == 0:
            raise BaseChartError("cols cannot be empty")

        if len(rows) > self.MAX_ROWS:
            raise BaseChartError("heatmap exceeds max rows")

        if len(cols) > self.MAX_COLS:
            raise BaseChartError("heatmap exceeds max columns")

        if len(matrix) != len(rows):
            raise BaseChartError("matrix row mismatch")

        for row in matrix:

            if not isinstance(row, list):
                raise BaseChartError("matrix rows must be lists")

            if len(row) != len(cols):
                raise BaseChartError("matrix column mismatch")

    # -------------------------------------------------
    # Set Heatmap Data
    # -------------------------------------------------

    def set_matrix(
        self,
        rows: List[str],
        cols: List[str],
        matrix: List[List[Number]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set heatmap matrix.

        Example
        -------
        rows = days of week
        cols = trading hours
        matrix = pnl values
        """

        self._validate_matrix(rows, cols, matrix)

        with self._data_lock:

            self._rows = list(rows)
            self._cols = list(cols)
            self._matrix = [list(r) for r in matrix]

            if metadata:
                self.set_metadata("heatmap_metadata", metadata)

    # -------------------------------------------------
    # Update Cell
    # -------------------------------------------------

    def update_cell(
        self,
        row_index: int,
        col_index: int,
        value: Number,
    ) -> None:
        """
        Safely update a heatmap cell.
        """

        with self._data_lock:

            if row_index >= len(self._matrix):
                raise BaseChartError("row index out of range")

            if col_index >= len(self._matrix[0]):
                raise BaseChartError("col index out of range")

            self._matrix[row_index][col_index] = value

    # -------------------------------------------------
    # Layout Helpers
    # -------------------------------------------------

    def configure_layout(
        self,
        x_label: str,
        y_label: str,
        color_scheme: str = "performance",
    ) -> None:

        self.set_layout(
            {
                "x_label": x_label,
                "y_label": y_label,
                "color_scheme": color_scheme,
            }
        )

    # -------------------------------------------------
    # Data Build
    # -------------------------------------------------

    def _build_data(self) -> Dict[str, Any]:

        with self._data_lock:

            return {
                "rows": list(self._rows),
                "cols": list(self._cols),
                "matrix": [list(r) for r in self._matrix],
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
            "chart_type": "heatmap",
            "rows": len(self._rows),
            "cols": len(self._cols),
            "timestamp": time.time(),
        }