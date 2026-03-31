from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, replace
from threading import RLock
from copy import deepcopy
from datetime import datetime, timezone

from execution_tools.market_spec_resolver import MarketSpecResolver
from execution_tools.trade_cost_engine import TradeCostEngine
from execution_tools.minimum_target_engine import MinimumTargetEngine
from models.position_plan import PositionPlan


class PositionSizerError(Exception):
    pass


# ==========================================================
# CONFIG MODEL (IMMUTABLE STYLE)
# ==========================================================

@dataclass(frozen=True)
class PositionSizerConfig:

    # Trade Limits
    max_number_of_trades: Optional[int] = None
    max_number_of_trades_per_symbol: Optional[int] = None

    # Volume Limits
    max_volume: Optional[float] = None
    max_volume_per_symbol: Optional[float] = None

    # Risk Limits
    max_risk_percent: Optional[float] = None
    max_risk_percent_per_symbol: Optional[float] = None
    max_risk_amount: Optional[float] = None

    # Execution Limits
    max_slippage_cost: Optional[float] = None
    max_spread: Optional[float] = None

    # Capital Controls
    max_daily_drawdown: Optional[float] = None
    max_weekly_drawdown: Optional[float] = None
    max_consecutive_losses: Optional[int] = None
    leverage_cap: Optional[float] = None
    max_open_positions: Optional[int] = None
    correlation_exposure_cap: Optional[float] = None
    regime_based_risk_multiplier: float = 1.0

    # Discipline Controls
    mandatory_checklist_completion: bool = False
    strict_mode_toggle: bool = False
    app_discipline_mode_enabled: bool = True
    position_sizer_discipline_enabled: bool = True
    cooldown_period_after_violation: Optional[int] = None
    cooldown_period_after_loss_streak: Optional[int] = None

    # Execution Guards
    slippage_guard_enabled: bool = True
    spread_guard_enabled: bool = True
    volatility_guard_enabled: bool = False


# ==========================================================
# POSITION SIZER ENGINE
# ==========================================================

class PositionSizer:

    def __init__(self):
        self._lock = RLock()
        self._config = PositionSizerConfig()
        self._last_update_time = None
        self._market_spec_resolver = MarketSpecResolver()
        self._trade_cost_engine = TradeCostEngine()
        self._minimum_target_engine = MinimumTargetEngine()

    # ======================================================
    # HOT-RELOAD SAFE CONFIG UPDATE
    # ======================================================

    def update_config(self, **kwargs):

        with self._lock:

            new_config = replace(self._config, **kwargs)

            self._validate_config(new_config)

            self._config = new_config
            self._last_update_time = datetime.now(timezone.utc)

    # ======================================================
    # VALIDATION LAYER
    # ======================================================

    def _validate_config(self, config: PositionSizerConfig):

        if config.max_risk_percent is not None:
            if not (0 < config.max_risk_percent <= 5):
                raise PositionSizerError("Invalid max_risk_percent")

        if config.leverage_cap is not None:
            if config.leverage_cap <= 0:
                raise PositionSizerError("Invalid leverage_cap")

        if config.regime_based_risk_multiplier <= 0:
            raise PositionSizerError("Invalid regime multiplier")

        if config.max_spread is not None and config.max_spread < 0:
            raise PositionSizerError("Invalid spread limit")

        if config.max_slippage_cost is not None and config.max_slippage_cost < 0:
            raise PositionSizerError("Invalid slippage cost")

        if config.max_number_of_trades is not None and config.max_number_of_trades < 0:
            raise PositionSizerError("Invalid max trades")

    # ======================================================
    # MT5-STYLE POSITION CALCULATION
    # ======================================================

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        symbol_volatility: Optional[float] = None,
        market_type: Optional[str] = None,
        instrument_overrides: Optional[Dict[str, Any]] = None,
    ) -> float:

        with self._lock:

            config = self._config

        risk_percent = config.max_risk_percent or 1.0

        risk_percent *= config.regime_based_risk_multiplier

        risk_amount = account_balance * (risk_percent / 100.0)

        if config.max_risk_amount:
            risk_amount = min(risk_amount, config.max_risk_amount)

        stop_distance = abs(entry_price - stop_loss_price)

        if stop_distance == 0:
            raise PositionSizerError("Stop loss distance cannot be zero")

        instrument = self._market_spec_resolver.resolve(
            symbol="N/A",
            market_type=market_type,
            instrument_overrides=instrument_overrides,
        )

        raw_volume = risk_amount / (stop_distance * instrument.contract_multiplier)

        if config.max_volume:
            raw_volume = min(raw_volume, config.max_volume)

        if config.leverage_cap:
            raw_volume = min(raw_volume, account_balance * config.leverage_cap)

        return round(raw_volume, 4)

    def preview_position_plan(
        self,
        account_balance: float,
        symbol: str,
        market_type: str,
        side: str,
        entry_price: float,
        stop_loss_price: float,
        target_price: Optional[float] = None,
        probability_bucket: Optional[str] = None,
        explicit_costs: Optional[Dict[str, Any]] = None,
        instrument_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        quantity = self.calculate_position_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            market_type=market_type,
            instrument_overrides=instrument_overrides,
        )

        instrument = self._market_spec_resolver.resolve(
            symbol=symbol,
            market_type=market_type,
            instrument_overrides=instrument_overrides,
        )
        required_capital = round(
            entry_price * quantity * instrument.contract_multiplier * instrument.margin_rate,
            6,
        )
        risk_amount = round(
            abs(entry_price - stop_loss_price) * quantity * instrument.contract_multiplier,
            6,
        )
        reward_amount = round(
            abs((target_price or entry_price) - entry_price)
            * quantity
            * instrument.contract_multiplier,
            6,
        )
        costs = self._trade_cost_engine.estimate_costs(
            entry_price=entry_price,
            quantity=quantity,
            instrument=instrument,
            explicit_costs=explicit_costs,
        )
        minimum_target_price = self._minimum_target_engine.get_minimum_target_price(
            probability_bucket=probability_bucket,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            quantity=quantity * instrument.contract_multiplier,
            side=side,
            total_costs=costs["total"],
        )
        minimum_target_reward = self._minimum_target_engine.get_required_reward(
            probability_bucket=probability_bucket,
            risk_amount=risk_amount,
            total_costs=costs["total"],
        )

        plan = PositionPlan(
            quantity=quantity,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            required_capital=required_capital,
            estimated_fees=costs["brokerage"] + costs["exchange_fees"] + costs["taxes"],
            estimated_slippage=costs["slippage"],
            estimated_total_cost=costs["total"],
            minimum_target_price=minimum_target_price,
            minimum_target_reward=minimum_target_reward,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            market_type=market_type,
            metadata={
                "symbol": symbol,
                "side": side,
                "instrument": instrument.to_dict(),
                "cost_breakdown": costs,
                "discipline_mode_enabled": self.is_discipline_mode_enabled(),
            },
        )
        return plan.to_dict()

    def is_discipline_mode_enabled(self) -> bool:
        with self._lock:
            config = self._config
        return bool(
            config.app_discipline_mode_enabled
            and config.position_sizer_discipline_enabled
        )

    # ======================================================
    # SNAPSHOT ACCESS
    # ======================================================

    def get_config(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(asdict(self._config))
