from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.heatmap import HeatmapChart
from visualization.charts.radar import RadarChart
from visualization.charts.pie import PieChart


class BehavioralDashboard:
    """
    Institutional Behavioral Dashboard

    Responsibilities
    ----------------
    • Visualize AI-detected psychological patterns
    • Remain deterministic and replay-safe
    • Operate without affecting trading engine
    • Integrate with AI behavioral analysis modules

    This module NEVER computes behavioral metrics.
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
    # Behavior Score Trend
    # -------------------------------------------------

    def build_behavior_score_trend(
        self,
        timestamps: List[Any],
        behavior_scores: List[float]
    ) -> None:

        chart = TimeSeriesChart(
            "Behavior Score Trend",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(
            "behavior_score",
            timestamps,
            behavior_scores
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Behavior Score"
        )

        with self._lock:
            self._charts["behavior_score_trend"] = chart.export()

    # -------------------------------------------------
    # Behavioral Trigger Breakdown
    # -------------------------------------------------

    def build_behavior_trigger_breakdown(
        self,
        trigger_names: List[str],
        trigger_counts: List[int]
    ) -> None:

        chart = BarChart(
            "Behavior Triggers",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_categories(trigger_names)

        chart.add_series(
            "trigger_count",
            trigger_counts
        )

        chart.configure_layout(
            x_label="Behavior Trigger",
            y_label="Occurrence Count"
        )

        with self._lock:
            self._charts["behavior_trigger_breakdown"] = chart.export()

    # -------------------------------------------------
    # Behavior Pattern Heatmap
    # -------------------------------------------------

    def build_behavior_pattern_heatmap(
        self,
        behaviors: List[str],
        periods: List[str],
        behavior_matrix: List[List[float]]
    ) -> None:

        chart = HeatmapChart(
            "Behavior Pattern Heatmap",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_matrix(
            rows=behaviors,
            cols=periods,
            matrix=behavior_matrix
        )

        chart.configure_layout(
            x_label="Time Period",
            y_label="Behavior"
        )

        with self._lock:
            self._charts["behavior_pattern_heatmap"] = chart.export()

    # -------------------------------------------------
    # Psychological Profile Radar
    # -------------------------------------------------

    def build_psychological_profile(
        self,
        traits: List[str],
        trait_scores: List[float]
    ) -> None:

        chart = RadarChart(
            "Psychological Profile",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_axes(traits)

        chart.add_profile(
            "Trader",
            trait_scores
        )

        chart.configure_layout(
            radial_min=0,
            radial_max=100
        )

        with self._lock:
            self._charts["psychological_profile"] = chart.export()

    # -------------------------------------------------
    # Behavior Category Distribution
    # -------------------------------------------------

    def build_behavior_distribution(
        self,
        categories: List[str],
        values: List[int]
    ) -> None:

        chart = PieChart(
            "Behavior Distribution",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_slices(
            labels=categories,
            values=values
        )

        chart.configure_layout(
            show_percentage=True
        )

        with self._lock:
            self._charts["behavior_distribution"] = chart.export()

    # -------------------------------------------------
    # Dashboard Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "behavioral",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata)
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "behavioral",
                "chart_count": len(self._charts),
                "timestamp": time.time()
            }