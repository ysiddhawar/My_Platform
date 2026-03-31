from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.radar import RadarChart
from visualization.charts.heatmap import HeatmapChart


class ComparisonDashboard:
    """
    Institutional Comparison Dashboard

    Responsibilities
    ----------------
    • Visualize comparisons across traders, strategies, or time periods
    • Show improvements or deterioration in performance
    • Integrate outputs from metrics, discipline, portfolio, capital and governance modules

    IMPORTANT
    ---------
    This module NEVER calculates metrics.
    It ONLY visualizes results produced by platform engines.
    """

    VERSION = 1

    def __init__(self, monitoring_registry: Optional[Any] = None):

        self._monitoring_registry = monitoring_registry

        self._charts: Dict[str, Any] = {}

        self._lock = threading.Lock()

        self._metadata = {
            "created_at": time.time(),
            "version": self.VERSION
        }

    # -------------------------------------------------
    # Performance Comparison
    # -------------------------------------------------

    def build_performance_comparison(
        self,
        timestamps: List[Any],
        series_a: List[float],
        series_b: List[float],
        label_a: str,
        label_b: str
    ) -> None:

        chart = TimeSeriesChart(
            "Performance Comparison",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(label_a, timestamps, series_a)
        chart.add_series(label_b, timestamps, series_b)

        chart.configure_axes(
            x_label="Time",
            y_label="Performance"
        )

        with self._lock:
            self._charts["performance_comparison"] = chart.export()

    # -------------------------------------------------
    # Metric Comparison
    # -------------------------------------------------

    def build_metric_comparison(
        self,
        metrics: List[str],
        values_a: List[float],
        values_b: List[float],
        label_a: str,
        label_b: str
    ) -> None:

        chart = BarChart(
            "Metric Comparison",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_categories(metrics)

        chart.add_series(label_a, values_a)
        chart.add_series(label_b, values_b)

        chart.configure_layout(
            x_label="Metric",
            y_label="Value"
        )

        with self._lock:
            self._charts["metric_comparison"] = chart.export()

    # -------------------------------------------------
    # Risk Comparison
    # -------------------------------------------------

    def build_risk_comparison(
        self,
        risk_metrics: List[str],
        values_a: List[float],
        values_b: List[float],
        label_a: str,
        label_b: str
    ) -> None:

        chart = RadarChart(
            "Risk Profile Comparison",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_axes(risk_metrics)

        chart.add_profile(label_a, values_a)
        chart.add_profile(label_b, values_b)

        chart.configure_layout(
            radial_min=0,
            radial_max=100
        )

        with self._lock:
            self._charts["risk_comparison"] = chart.export()

    # -------------------------------------------------
    # Behavioral Comparison
    # -------------------------------------------------

    def build_behavior_comparison(
        self,
        behaviors: List[str],
        matrix: List[List[float]]
    ) -> None:

        chart = HeatmapChart(
            "Behavior Pattern Comparison",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_matrix(
            rows=behaviors,
            cols=["Baseline", "Current"],
            matrix=matrix
        )

        chart.configure_layout(
            x_label="Period",
            y_label="Behavior Pattern"
        )

        with self._lock:
            self._charts["behavior_comparison"] = chart.export()

    # -------------------------------------------------
    # Capital Comparison
    # -------------------------------------------------

    def build_capital_comparison(
        self,
        timestamps: List[Any],
        capital_a: List[float],
        capital_b: List[float],
        label_a: str,
        label_b: str
    ) -> None:

        chart = TimeSeriesChart(
            "Capital Growth Comparison",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(label_a, timestamps, capital_a)
        chart.add_series(label_b, timestamps, capital_b)

        chart.configure_axes(
            x_label="Time",
            y_label="Capital"
        )

        with self._lock:
            self._charts["capital_comparison"] = chart.export()

    # -------------------------------------------------
    # Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "comparison",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata)
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "comparison",
                "chart_count": len(self._charts),
                "timestamp": time.time()
            }