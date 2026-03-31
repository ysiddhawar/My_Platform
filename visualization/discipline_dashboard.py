from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.heatmap import HeatmapChart
from visualization.charts.radar import RadarChart


class DisciplineDashboard:
    """
    Institutional Discipline Dashboard

    Responsibilities
    ----------------
    • Visualize trader discipline metrics
    • Remain deterministic and replay-safe
    • Operate without affecting execution engine
    • Integrate with discipline module outputs

    This module NEVER computes discipline metrics.
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
    # Discipline Score Trend
    # -------------------------------------------------

    def build_discipline_score_trend(
        self,
        timestamps: List[Any],
        discipline_scores: List[float]
    ) -> None:

        chart = TimeSeriesChart(
            "Discipline Score Trend",
            monitoring_registry=self._monitoring_registry
        )

        chart.add_series(
            "discipline_score",
            timestamps,
            discipline_scores
        )

        chart.configure_axes(
            x_label="Time",
            y_label="Discipline Score"
        )

        with self._lock:
            self._charts["discipline_score_trend"] = chart.export()

    # -------------------------------------------------
    # Checklist Compliance
    # -------------------------------------------------

    def build_checklist_compliance(
        self,
        checklist_items: List[str],
        compliance_rates: List[float]
    ) -> None:

        chart = BarChart(
            "Checklist Compliance",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_categories(checklist_items)

        chart.add_series(
            "compliance_rate",
            compliance_rates
        )

        chart.configure_layout(
            x_label="Checklist Item",
            y_label="Compliance %"
        )

        with self._lock:
            self._charts["checklist_compliance"] = chart.export()

    # -------------------------------------------------
    # Rule Violations Breakdown
    # -------------------------------------------------

    def build_rule_violation_breakdown(
        self,
        rule_names: List[str],
        violation_counts: List[int]
    ) -> None:

        chart = BarChart(
            "Rule Violations",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_categories(rule_names)

        chart.add_series(
            "violations",
            violation_counts
        )

        chart.configure_layout(
            x_label="Rule",
            y_label="Violation Count"
        )

        with self._lock:
            self._charts["rule_violation_breakdown"] = chart.export()

    # -------------------------------------------------
    # Violation Heatmap
    # -------------------------------------------------

    def build_violation_heatmap(
        self,
        rules: List[str],
        time_periods: List[str],
        violation_matrix: List[List[int]]
    ) -> None:

        chart = HeatmapChart(
            "Violation Heatmap",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_matrix(
            rows=rules,
            cols=time_periods,
            matrix=violation_matrix
        )

        chart.configure_layout(
            x_label="Time Period",
            y_label="Rule"
        )

        with self._lock:
            self._charts["violation_heatmap"] = chart.export()

    # -------------------------------------------------
    # Discipline Radar Profile
    # -------------------------------------------------

    def build_discipline_profile(
        self,
        metrics: List[str],
        values: List[float]
    ) -> None:

        chart = RadarChart(
            "Discipline Profile",
            monitoring_registry=self._monitoring_registry
        )

        chart.set_axes(metrics)

        chart.add_profile(
            "Trader",
            values
        )

        chart.configure_layout(
            radial_min=0,
            radial_max=100
        )

        with self._lock:
            self._charts["discipline_profile"] = chart.export()

    # -------------------------------------------------
    # Dashboard Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "discipline",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata)
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:

            return {
                "dashboard_type": "discipline",
                "chart_count": len(self._charts),
                "timestamp": time.time()
            }