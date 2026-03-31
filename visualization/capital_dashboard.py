from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.pie import PieChart
from visualization.charts.radar import RadarChart


class CapitalDashboard:
    """
    Institutional Capital Dashboard

    Responsibilities
    ----------------
    • Visualize capital allocation and growth
    • Integrate with capital management modules
    • Remain deterministic and replay-safe
    • Remain thread-safe and non-blocking

    IMPORTANT:
    This module NEVER calculates capital metrics.
    It only visualizes outputs produced by capital modules.
    """

    VERSION = 1

    def __init__(self, monitoring_registry: Optional[Any] = None):

        self._monitoring_registry = monitoring_registry

        self._charts: Dict[str, Any] = {}

        self._lock = threading.Lock()

        self._metadata = {
            "created_at": time.time(),
            "version": self.VERSION,
        }

    # -------------------------------------------------
    # Capital Growth Curve
    # -------------------------------------------------

    def build_capital_growth(
        self,
        timestamps: List[Any],
        capital_values: List[float],
    ) -> None:

        chart = TimeSeriesChart(
            "Capital Growth",
            monitoring_registry=self._monitoring_registry,
        )

        chart.add_series(
            "capital",
            timestamps,
            capital_values,
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Capital Value",
        )

        with self._lock:
            self._charts["capital_growth"] = chart.export()

    # -------------------------------------------------
    # Risk Budget Allocation
    # -------------------------------------------------

    def build_risk_budget_allocation(
        self,
        strategies: List[str],
        allocations: List[float],
    ) -> None:

        chart = PieChart(
            "Risk Budget Allocation",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_slices(
            labels=strategies,
            values=allocations,
        )

        chart.configure_layout(show_percentage=True)

        with self._lock:
            self._charts["risk_budget_allocation"] = chart.export()

    # -------------------------------------------------
    # Position Size Distribution
    # -------------------------------------------------

    def build_position_size_distribution(
        self,
        symbols: List[str],
        position_sizes: List[float],
    ) -> None:

        chart = BarChart(
            "Position Size Distribution",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_categories(symbols)

        chart.add_series(
            "position_size",
            position_sizes,
        )

        chart.configure_layout(
            x_label="Symbol",
            y_label="Position Size",
        )

        with self._lock:
            self._charts["position_size_distribution"] = chart.export()

    # -------------------------------------------------
    # Leverage Utilization
    # -------------------------------------------------

    def build_leverage_usage(
        self,
        timestamps: List[Any],
        leverage_values: List[float],
    ) -> None:

        chart = TimeSeriesChart(
            "Leverage Utilization",
            monitoring_registry=self._monitoring_registry,
        )

        chart.add_series(
            "leverage",
            timestamps,
            leverage_values,
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Leverage",
        )

        with self._lock:
            self._charts["leverage_usage"] = chart.export()

    # -------------------------------------------------
    # Capital Efficiency Radar
    # -------------------------------------------------

    def build_capital_efficiency_profile(
        self,
        metrics: List[str],
        values: List[float],
    ) -> None:

        chart = RadarChart(
            "Capital Efficiency",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_axes(metrics)

        chart.add_profile(
            "Capital Efficiency",
            values,
        )

        chart.configure_layout(
            radial_min=0,
            radial_max=100,
        )

        with self._lock:
            self._charts["capital_efficiency_profile"] = chart.export()

    # -------------------------------------------------
    # Dashboard Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "capital",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata),
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "capital",
                "chart_count": len(self._charts),
                "timestamp": time.time(),
            }