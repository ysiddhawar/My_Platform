from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, replace
from threading import RLock
from copy import deepcopy
from datetime import datetime, timezone


class RiskLineManagerError(Exception):
    pass


# ==========================================================
# CONFIG MODEL (IMMUTABLE)
# ==========================================================

@dataclass(frozen=True)
class RiskLineConfig:

    # Drawdown Limits
    max_daily_drawdown: Optional[float] = None
    max_weekly_drawdown: Optional[float] = None

    # Loss Limits
    max_consecutive_losses: Optional[int] = None

    # Exposure Limits
    max_open_positions: Optional[int] = None
    correlation_exposure_cap: Optional[float] = None

    # Cooldown Controls
    cooldown_period: Optional[int] = None  # seconds

    # Internal toggles
    enabled: bool = True


# ==========================================================
# RISK LINE MANAGER
# ==========================================================

class RiskLineManager:

    def __init__(self):
        self._lock = RLock()
        self._config = RiskLineConfig()
        self._last_update_time = None

        # Runtime tracking (not config)
        self._daily_drawdown = 0.0
        self._weekly_drawdown = 0.0
        self._consecutive_losses = 0
        self._last_violation_timestamp = None

    # ======================================================
    # HOT RELOAD SAFE CONFIG UPDATE
    # ======================================================

    def update_config(self, **kwargs):

        with self._lock:

            new_config = replace(self._config, **kwargs)
            self._validate_config(new_config)

            self._config = new_config
            self._last_update_time = datetime.now(timezone.utc)

    # ======================================================
    # VALIDATION
    # ======================================================

    def _validate_config(self, config: RiskLineConfig):

        if config.max_daily_drawdown is not None and config.max_daily_drawdown < 0:
            raise RiskLineManagerError("Invalid max_daily_drawdown")

        if config.max_weekly_drawdown is not None and config.max_weekly_drawdown < 0:
            raise RiskLineManagerError("Invalid max_weekly_drawdown")

        if config.max_consecutive_losses is not None and config.max_consecutive_losses < 0:
            raise RiskLineManagerError("Invalid max_consecutive_losses")

        if config.max_open_positions is not None and config.max_open_positions < 0:
            raise RiskLineManagerError("Invalid max_open_positions")

        if config.correlation_exposure_cap is not None:
            if not (0 <= config.correlation_exposure_cap <= 1):
                raise RiskLineManagerError("Invalid correlation_exposure_cap")

    # ======================================================
    # RUNTIME TRACKING
    # ======================================================

    def record_trade_result(self, pnl: float):

        with self._lock:

            if pnl < 0:
                self._consecutive_losses += 1
            else:
                self._consecutive_losses = 0

    def update_drawdown(self, daily_dd: float, weekly_dd: float):

        with self._lock:
            self._daily_drawdown = daily_dd
            self._weekly_drawdown = weekly_dd

    # ======================================================
    # RISK VALIDATION
    # ======================================================

    def is_trade_allowed(
        self,
        open_positions: int,
        correlation_exposure: Optional[float] = None,
    ) -> bool:

        with self._lock:

            config = self._config

            if not config.enabled:
                return True

            if config.max_daily_drawdown is not None:
                if self._daily_drawdown >= config.max_daily_drawdown:
                    return False

            if config.max_weekly_drawdown is not None:
                if self._weekly_drawdown >= config.max_weekly_drawdown:
                    return False

            if config.max_consecutive_losses is not None:
                if self._consecutive_losses >= config.max_consecutive_losses:
                    return False

            if config.max_open_positions is not None:
                if open_positions >= config.max_open_positions:
                    return False

            if correlation_exposure is not None and config.correlation_exposure_cap is not None:
                if correlation_exposure >= config.correlation_exposure_cap:
                    return False

            return True

    # ======================================================
    # SNAPSHOT
    # ======================================================

    def get_config(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(asdict(self._config))
