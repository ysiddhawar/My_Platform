from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.pie import PieChart
from visualization.charts.heatmap import HeatmapChart


class PerformanceDashboard:
    """
    Institutional Trader Performance Dashboard

    Responsibilities
    ----------------
    • Visualize trader performance metrics
    • Build deterministic dashboard outputs
    • Remain non-blocking and thread-safe
    • Integrate with metrics engine outputs

    This module NEVER computes metrics.
    It only visualizes them.
    """

    VERSION = 1

    def __init__(
        self,
        monitoring_registry: Optional[Any] = None
    ):

        self._monitoring_registry = monitoring_registry

        self._charts: Dict[str, Any] = {}

        self._lock = threading.Lock()

        self._metadata = {
            "created_at": time.time(),
            "version": self.VERSION
        }

    # -------------------------------------------------
    # Equity Curve
    # -------------------------------------------------

    def build_equity_curve(
        self,
        timestamps: List[Any],
        equity_curve: List[float]
    ) -> None:

        chart = TimeSeriesChart(
            "Equity Curve",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(
            "equity",
            timestamps,
            equity_curve
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Equity"
        )

        with self._lock:
            self._charts["equity_curve"] = chart.export()

    # -------------------------------------------------
    # Drawdown Curve
    # -------------------------------------------------

    def build_drawdown_curve(
        self,
        timestamps: List[Any],
        drawdown: List[float]
    ) -> None:

        chart = TimeSeriesChart(
            "Drawdown Curve",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(
            "drawdown",
            timestamps,
            drawdown
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Drawdown"
        )

        with self._lock:
            self._charts["drawdown_curve"] = chart.export()

    # -------------------------------------------------
    # Rolling Sharpe
    # -------------------------------------------------

    def build_rolling_sharpe(
        self,
        timestamps: List[Any],
        sharpe_values: List[float]
    ) -> None:

        chart = TimeSeriesChart(
            "Rolling Sharpe",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(
            "rolling_sharpe",
            timestamps,
            sharpe_values
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Sharpe"
        )

        with self._lock:
            self._charts["rolling_sharpe"] = chart.export()

    # -------------------------------------------------
    # Strategy Comparison
    # -------------------------------------------------

    def build_strategy_comparison(
        self,
        strategy_names: List[str],
        profits: List[float]
    ) -> None:

        chart = BarChart(
            "Strategy Performance",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_categories(strategy_names)

        chart.add_series(
            "profit",
            profits
        )

        chart.configure_layout(
            x_label="Strategy",
            y_label="Profit"
        )

        with self._lock:
            self._charts["strategy_comparison"] = chart.export()

    # -------------------------------------------------
    # Win / Loss Distribution
    # -------------------------------------------------

    def build_win_loss_distribution(
        self,
        wins: int,
        losses: int
    ) -> None:

        chart = PieChart(
            "Win / Loss Distribution",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_slices(
            labels=["Wins", "Losses"],
            values=[wins, losses]
        )

        chart.configure_layout(
            show_percentage=True
        )

        with self._lock:
            self._charts["win_loss_distribution"] = chart.export()

    # -------------------------------------------------
    # Day-of-Week Heatmap
    # -------------------------------------------------

    def build_day_of_week_heatmap(
        self,
        days: List[str],
        sessions: List[str],
        pnl_matrix: List[List[float]]
    ) -> None:

        chart = HeatmapChart(
            "Day of Week Performance",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_matrix(
            rows=days,
            cols=sessions,
            matrix=pnl_matrix
        )

        chart.configure_layout(
            x_label="Session",
            y_label="Day"
        )

        with self._lock:
            self._charts["day_of_week_heatmap"] = chart.export()

    # -------------------------------------------------
    # Dashboard Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "performance",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata)
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "performance",
                "chart_count": len(self._charts),
                "timestamp": time.time()
            }