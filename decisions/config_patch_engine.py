from __future__ import annotations

import copy
import time
from typing import Dict, Any, Optional, Callable


class ConfigPatchError(Exception):
    pass


class ConfigPatchEngine:
    """
    Institutional Safe Config Patch Engine

    Responsibilities:
    - Accept AI-generated config patch
    - Validate against strict whitelist
    - Validate numeric bounds
    - Apply patch to:
        • position_sizer
        • risk_line_manager
        • slippage_guard
    - Persist change via config_repository
    - Log change via event_store
    - Support rollback
    - Remain deterministic + replay-safe
    """

    VERSION = 1

    # ------------------------------------------------------------
    # STRICT WHITELIST (ONLY THESE CAN BE AUTO-UPDATED)
    # ------------------------------------------------------------

    ALLOWED_KEYS = {
        # Position Sizer
        "max_risk_percent",
        "max_risk_percent_per_symbol",
        "max_number_of_trades",
        "max_number_of_trades_per_symbol",
        "max_volume",
        "max_volume_per_symbol",
        "max_risk_amount",

        # Risk Controls
        "max_daily_drawdown",
        "max_weekly_drawdown",
        "max_consecutive_losses",

        # Execution Controls
        "max_slippage_cost",
        "max_spread",
    }

    # Absolute hard safety bounds
    BOUNDS = {
        "max_risk_percent": (0.0001, 0.05),
        "max_risk_percent_per_symbol": (0.0001, 0.05),
        "max_daily_drawdown": (0.001, 0.2),
        "max_weekly_drawdown": (0.005, 0.5),
        "max_consecutive_losses": (1, 20),
        "max_number_of_trades": (1, 1000),
        "max_number_of_trades_per_symbol": (1, 500),
        "max_volume": (0.0001, 1_000_000),
        "max_volume_per_symbol": (0.0001, 1_000_000),
        "max_risk_amount": (0.0001, 1_000_000),
        "max_slippage_cost": (0.0, 10_000),
        "max_spread": (0.0, 1000),
    }

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------

    def __init__(
        self,
        position_sizer: Any,
        risk_line_manager: Any,
        slippage_guard: Any,
        config_repository: Optional[Any] = None,
        event_store: Optional[Any] = None,
    ):
        self._position_sizer = position_sizer
        self._risk_line_manager = risk_line_manager
        self._slippage_guard = slippage_guard
        self._config_repository = config_repository
        self._event_store = event_store

    # ------------------------------------------------------------
    # PUBLIC APPLY METHOD
    # ------------------------------------------------------------

    def apply_patch(
        self,
        patch: Dict[str, Any],
        user_id: str,
        reason: str = "AI_prescription",
    ) -> Dict[str, Any]:

        if not isinstance(patch, dict):
            raise ConfigPatchError("Patch must be dict")

        safe_patch = self._validate_patch(patch)

        previous_config = self._snapshot_current_config()

        # Apply to live components (hot-reload compatible)
        self._position_sizer.update_config(safe_patch)
        self._risk_line_manager.update_config(safe_patch)
        self._slippage_guard.update_config(safe_patch)

        # Persist
        if self._config_repository:
            self._config_repository.save_config(user_id, safe_patch)

        # Log event
        if self._event_store:
            self._event_store.append_event({
                "type": "config_patch_applied",
                "user_id": user_id,
                "patch": safe_patch,
                "reason": reason,
                "timestamp": time.time(),
                "version": self.VERSION,
            })

        return {
            "status": "success",
            "applied_patch": safe_patch,
            "previous_config_snapshot": previous_config,
            "version": self.VERSION,
        }

    # ------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------

    def rollback(
        self,
        snapshot: Dict[str, Any],
        user_id: str,
    ):

        if not isinstance(snapshot, dict):
            raise ConfigPatchError("Invalid snapshot")

        self._position_sizer.update_config(snapshot)
        self._risk_line_manager.update_config(snapshot)
        self._slippage_guard.update_config(snapshot)

        if self._config_repository:
            self._config_repository.save_config(user_id, snapshot)

        if self._event_store:
            self._event_store.append_event({
                "type": "config_patch_rollback",
                "user_id": user_id,
                "timestamp": time.time(),
                "version": self.VERSION,
            })

    # ------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------

    def _validate_patch(self, patch: Dict[str, Any]) -> Dict[str, Any]:

        safe_patch = {}

        for key, value in patch.items():

            if key not in self.ALLOWED_KEYS:
                raise ConfigPatchError(f"Unauthorized config key: {key}")

            if key in self.BOUNDS:
                lower, upper = self.BOUNDS[key]

                if not isinstance(value, (int, float)):
                    raise ConfigPatchError(f"Invalid type for {key}")

                if not (lower <= value <= upper):
                    raise ConfigPatchError(
                        f"{key} out of allowed bounds ({lower}, {upper})"
                    )

            safe_patch[key] = value

        return safe_patch

    # ------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------

    def _snapshot_current_config(self) -> Dict[str, Any]:

        snapshot = {}

        if hasattr(self._position_sizer, "get_config"):
            snapshot.update(self._position_sizer.get_config())

        return copy.deepcopy(snapshot)