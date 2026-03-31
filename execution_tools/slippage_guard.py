from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, replace
from threading import RLock
from copy import deepcopy
from datetime import datetime, timezone


class SlippageGuardError(Exception):
    pass


# ==========================================================
# CONFIG MODEL
# ==========================================================

@dataclass(frozen=True)
class SlippageGuardConfig:

    max_slippage_cost: Optional[float] = None
    max_spread: Optional[float] = None

    slippage_guard_enabled: bool = True
    spread_guard_enabled: bool = True
    volatility_guard_enabled: bool = False


# ==========================================================
# SLIPPAGE GUARD
# ==========================================================

class SlippageGuard:

    def __init__(self):
        self._lock = RLock()
        self._config = SlippageGuardConfig()
        self._last_update_time = None

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

    def _validate_config(self, config: SlippageGuardConfig):

        if config.max_slippage_cost is not None and config.max_slippage_cost < 0:
            raise SlippageGuardError("Invalid max_slippage_cost")

        if config.max_spread is not None and config.max_spread < 0:
            raise SlippageGuardError("Invalid max_spread")

    # ======================================================
    # EXECUTION VALIDATION
    # ======================================================

    def is_execution_allowed(
        self,
        slippage_cost: Optional[float] = None,
        spread: Optional[float] = None,
        volatility: Optional[float] = None,
    ) -> bool:

        with self._lock:

            config = self._config

            if config.slippage_guard_enabled and config.max_slippage_cost is not None:
                if slippage_cost is not None and slippage_cost > config.max_slippage_cost:
                    return False

            if config.spread_guard_enabled and config.max_spread is not None:
                if spread is not None and spread > config.max_spread:
                    return False

            if config.volatility_guard_enabled:
                if volatility is not None and volatility <= 0:
                    return False

            return True

    # ======================================================
    # SNAPSHOT
    # ======================================================

    def get_config(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(asdict(self._config))
