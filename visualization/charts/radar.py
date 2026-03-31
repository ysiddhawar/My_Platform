from __future__ import annotations

import threading
import time
from typing import List, Dict, Any, Optional, Union

from visualization.charts.base_chart import BaseChart, BaseChartError


Number = Union[int, float]


class RadarChart(BaseChart):
    """
    Institutional Radar Chart

    Used For
    --------
    • Discipline profile
    • Strategy strength profile
    • Behavioral analysis
    • Risk factor exposure
    • Performance multi-metric comparison

    Design Goals
    ------------
    • Deterministic output
    • Thread-safe
    • Non-blocking
    • Replay-safe
    """

    MAX_AXES = 100

    def __init__(
        self,
        title: str,
        monitoring_registry: Optional[Any] = None,
    ):
        super().__init__(
            chart_type="radar",
            title=title,
            monitoring_registry=monitoring_registry,
        )

        self._axes: List[str] = []
        self._profiles: Dict[str, Dict[str, Any]] = {}

        self._data_lock = threading.Lock()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def _validate_axes(self, axes: List[str]) -> None:

        if not isinstance(axes, list):
            raise BaseChartError("axes must be list")

        if len(axes) == 0:
            raise BaseChartError("axes cannot be empty")

        if len(axes) > self.MAX_AXES:
            raise BaseChartError("too many radar axes")

    def _validate_values(self, values: List[Number]) -> None:

        if not isinstance(values, list):
            raise BaseChartError("values must be list")

        for v in values:
            if not isinstance(v, (int, float)):
                raise BaseChartError("radar values must be numeric")

    # -------------------------------------------------
    # Axis Management
    # -------------------------------------------------

    def set_axes(
        self,
        axes: List[str],
    ) -> None:
        """
        Define radar dimensions.

        Example:
        --------
        Discipline metrics
        Strategy strength metrics
        Behavioral factors
        """

        self._validate_axes(axes)

        with self._data_lock:
            self._axes = list(axes)

    # -------------------------------------------------
    # Profile Management
    # -------------------------------------------------

    def add_profile(
        self,
        name: str,
        values: List[Number],
        color: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add radar profile.

        Example
        -------
        Trader profile
        Strategy profile
        """

        if not name:
            raise BaseChartError("profile name required")

        self._validate_values(values)

        with self._data_lock:

            if not self._axes:
                raise BaseChartError("set axes before adding profiles")

            if len(values) != len(self._axes):
                raise BaseChartError("values must match axis count")

            self._profiles[name] = {
                "values": list(values),
                "color": color,
                "metadata": metadata or {},
            }

    # -------------------------------------------------
    # Update Value
    # -------------------------------------------------

    def update_value(
        self,
        profile_name: str,
        axis_index: int,
        value: Number,
    ) -> None:

        with self._data_lock:

            if profile_name not in self._profiles:
                raise BaseChartError("profile not found")

            if axis_index >= len(self._axes):
                raise BaseChartError("axis index out of range")

            self._profiles[profile_name]["values"][axis_index] = value

    # -------------------------------------------------
    # Layout
    # -------------------------------------------------

    def configure_layout(
        self,
        radial_min: Number = 0,
        radial_max: Optional[Number] = None,
    ) -> None:

        self.set_layout(
            {
                "radial_min": radial_min,
                "radial_max": radial_max,
            }
        )

    # -------------------------------------------------
    # Data Build
    # -------------------------------------------------

    def _build_data(self) -> Dict[str, Any]:

        with self._data_lock:

            profiles_output = []

            for name, profile in self._profiles.items():

                profiles_output.append(
                    {
                        "name": name,
                        "values": list(profile["values"]),
                        "color": profile.get("color"),
                        "metadata": profile.get("metadata", {}),
                    }
                )

            return {
                "axes": list(self._axes),
                "profiles": profiles_output,
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
            "chart_type": "radar",
            "axes": len(self._axes),
            "profiles": len(self._profiles),
            "timestamp": time.time(),
        }