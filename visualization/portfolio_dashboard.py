from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional, List

from visualization.charts.time_series import TimeSeriesChart
from visualization.charts.bar import BarChart
from visualization.charts.heatmap import HeatmapChart
from visualization.charts.radar import RadarChart
from visualization.charts.pie import PieChart


class PortfolioDashboard:
    """
    Institutional Portfolio Dashboard

    Responsibilities
    ----------------
    • Visualize portfolio analytics
    • Maintain deterministic outputs
    • Remain thread-safe and non-blocking
    • Integrate with portfolio analytics modules

    This module NEVER computes portfolio metrics.
    It only visualizes them.
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
    # Portfolio Value Trend
    # -------------------------------------------------

    def build_portfolio_value_trend(
        self,
        timestamps: List[Any],
        portfolio_values: List[float],
    ) -> None:

        chart = TimeSeriesChart(
            "Portfolio Value",
            monitoring_registry=self._monitoring_registry,
        )

        chart.add_series("portfolio_value", timestamps, portfolio_values)

        chart.configure_axes(
            x_label="Time",
            y_label="Portfolio Value",
        )

        with self._lock:
            self._charts["portfolio_value_trend"] = chart.export()

    # -------------------------------------------------
    # Portfolio Exposure Distribution
    # -------------------------------------------------

    def build_portfolio_exposure(
        self,
        symbols: List[str],
        exposures: List[float],
    ) -> None:

        chart = PieChart(
            "Portfolio Exposure",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_slices(
            labels=symbols,
            values=exposures,
        )

        chart.configure_layout(show_percentage=True)

        with self._lock:
            self._charts["portfolio_exposure"] = chart.export()

    # -------------------------------------------------
    # Correlation Heatmap
    # -------------------------------------------------

    def build_correlation_heatmap(
        self,
        assets: List[str],
        correlation_matrix: List[List[float]],
    ) -> None:

        chart = HeatmapChart(
            "Asset Correlation",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_matrix(
            rows=assets,
            cols=assets,
            matrix=correlation_matrix,
        )

        chart.configure_layout(
            x_label="Asset",
            y_label="Asset",
        )

        with self._lock:
            self._charts["correlation_heatmap"] = chart.export()

    # -------------------------------------------------
    # Risk Contribution
    # -------------------------------------------------

    def build_risk_contribution(
        self,
        assets: List[str],
        risk_contributions: List[float],
    ) -> None:

        chart = BarChart(
            "Risk Contribution",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_categories(assets)

        chart.add_series(
            "risk_contribution",
            risk_contributions,
        )

        chart.configure_layout(
            x_label="Asset",
            y_label="Risk Contribution",
        )

        with self._lock:
            self._charts["risk_contribution"] = chart.export()

    # -------------------------------------------------
    # Diversification Profile
    # -------------------------------------------------

    def build_diversification_profile(
        self,
        metrics: List[str],
        values: List[float],
    ) -> None:

        chart = RadarChart(
            "Diversification Profile",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_axes(metrics)

        chart.add_profile(
            "Portfolio",
            values,
        )

        chart.configure_layout(
            radial_min=0,
            radial_max=100,
        )

        with self._lock:
            self._charts["diversification_profile"] = chart.export()

    # -------------------------------------------------
    # Fragility Indicators
    # -------------------------------------------------

    def build_fragility_indicators(
        self,
        indicators: List[str],
        values: List[float],
    ) -> None:

        chart = BarChart(
            "Portfolio Fragility Indicators",
            monitoring_registry=self._monitoring_registry,
        )

        chart.set_categories(indicators)

        chart.add_series(
            "fragility_score",
            values,
        )

        chart.configure_layout(
            x_label="Indicator",
            y_label="Score",
        )

        with self._lock:
            self._charts["fragility_indicators"] = chart.export()

    # -------------------------------------------------
    # Dashboard Export
    # -------------------------------------------------

    def export(self) -> Dict[str, Any]:

        with self._lock:
            return {
                "dashboard_type": "portfolio",
                "charts": dict(self._charts),
                "metadata": dict(self._metadata),
            }

    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        with self._lock:
            return {
                "dashboard_type": "portfolio",
                "chart_count": len(self._charts),
                "timestamp": time.time(),
            }