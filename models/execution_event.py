from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


class ExecutionEventValidationError(Exception):
    pass


class ExecutionEvent:
    """
    Institutional-Grade Execution Event

    Represents a PRE-TRADE intent event before execution.

    Used by:
    - Discipline engine
    - Strict mode gatekeeper
    - Position sizing engine
    - Risk control engine
    - Decision governance layer

    This object exists BEFORE Trade snapshot creation.
    """

    __slots__ = (
        # Envelope compatibility
        "_event_type",
        "_timestamp",

        # Identity
        "_event_id",
        "_created_at",

        # Account / Broker
        "_account_id",
        "_broker_id",

        # Instrument
        "_symbol",
        "_market_type",
        "_side",

        # Strategy
        "_strategy_tag",
        "_setup_name",

        # Intended Order Parameters
        "_intended_entry_price",
        "_intended_stop_loss",
        "_intended_target",
        "_intended_quantity",
        "_intended_lot_size",
        "_intended_leverage",

        # Risk Settings
        "_risk_percent",
        "_risk_amount",
        "_max_slippage_allowed",

        # Behavioral Input
        "_selected_checklist",
        "_probability_bucket",
        "_discipline_mode_enabled",
        "_mandatory_checklist",
        "_confidence_score",
        "_emotion_tag",

        # Environment Snapshot (at trigger time)
        "_volatility_regime",
        "_equity_snapshot",
        "_drawdown_snapshot",
        "_open_positions_count",
        "_correlation_exposure_snapshot",

        # Governance
        "_violations_detected",
        "_strict_mode",
        "_approved",
        "_rejection_reason",

        # System
        "_metadata",
        "_finalized",
    )

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        account_id: Optional[str] = None,
        broker_id: Optional[str] = None,
        symbol: Optional[str] = None,
        market_type: Optional[str] = None,
        side: Optional[str] = None,
        strategy_tag: Optional[str] = None,
        setup_name: Optional[str] = None,
        intended_entry_price: Optional[float] = None,
        intended_quantity: Optional[float] = None,
        intended_lot_size: Optional[float] = None,
        intended_leverage: Optional[float] = None,
        intended_stop_loss: Optional[float] = None,
        intended_target: Optional[float] = None,
        risk_percent: Optional[float] = None,
        risk_amount: Optional[float] = None,
        max_slippage_allowed: Optional[float] = None,
        selected_checklist: Optional[List[str]] = None,
        probability_bucket: Optional[str] = None,
        discipline_mode_enabled: bool = False,
        mandatory_checklist: Optional[List[str]] = None,
        confidence_score: Optional[float] = None,
        emotion_tag: Optional[str] = None,
        volatility_regime: Optional[str] = None,
        equity_snapshot: Optional[float] = None,
        drawdown_snapshot: Optional[float] = None,
        open_positions_count: Optional[int] = None,
        correlation_exposure_snapshot: Optional[Dict[str, float]] = None,
        strict_mode: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        event_type: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):

        # Identity
        self._event_id = str(uuid.uuid4())
        self._created_at = datetime.now(timezone.utc)
        self._event_type = event_type or "PRE_TRADE_REQUEST"
        self._timestamp = timestamp or self._created_at

        # Envelope mode compatibility:
        # many modules use ExecutionEvent(event_type=..., timestamp=..., metadata=...).
        if event_type is not None:
            self._account_id = account_id or "SYSTEM"
            self._broker_id = broker_id or "SYSTEM"
            self._symbol = symbol or "N/A"
            self._market_type = market_type or "N/A"
            self._side = side or "buy"
            self._strategy_tag = strategy_tag or "N/A"
            self._setup_name = setup_name or "N/A"
            self._intended_entry_price = float(intended_entry_price or 1.0)
            self._intended_stop_loss = intended_stop_loss
            self._intended_target = intended_target
            self._intended_quantity = float(intended_quantity or 1.0)
            self._intended_lot_size = float(intended_lot_size or 1.0)
            self._intended_leverage = float(intended_leverage or 1.0)
            self._risk_percent = risk_percent
            self._risk_amount = risk_amount
            self._max_slippage_allowed = max_slippage_allowed
            self._selected_checklist = selected_checklist or []
            self._probability_bucket = probability_bucket
            self._discipline_mode_enabled = bool(discipline_mode_enabled)
            self._mandatory_checklist = mandatory_checklist or []
            self._confidence_score = confidence_score
            self._emotion_tag = emotion_tag
            self._volatility_regime = volatility_regime
            self._equity_snapshot = equity_snapshot
            self._drawdown_snapshot = drawdown_snapshot
            self._open_positions_count = open_positions_count
            self._correlation_exposure_snapshot = correlation_exposure_snapshot or {}
            self._violations_detected = []
            self._strict_mode = strict_mode
            self._approved = None
            self._rejection_reason = None
            self._metadata = metadata or {}
            self._finalized = False
            return

        # Account
        self._account_id = self._validate_non_empty(account_id, "account_id")
        self._broker_id = self._validate_non_empty(broker_id, "broker_id")

        # Instrument
        self._symbol = self._validate_non_empty(symbol, "symbol")
        self._market_type = self._validate_non_empty(market_type, "market_type")
        self._side = self._validate_side(side)

        # Strategy
        self._strategy_tag = self._validate_non_empty(strategy_tag, "strategy_tag")
        self._setup_name = self._validate_non_empty(setup_name, "setup_name")

        # Order Intent
        self._intended_entry_price = self._validate_positive(
            intended_entry_price, "intended_entry_price"
        )
        self._intended_quantity = self._validate_positive(
            intended_quantity, "intended_quantity"
        )
        self._intended_lot_size = self._validate_positive(
            intended_lot_size, "intended_lot_size"
        )
        self._intended_leverage = self._validate_positive(
            intended_leverage, "intended_leverage"
        )

        self._intended_stop_loss = intended_stop_loss
        self._intended_target = intended_target

        # Risk
        self._risk_percent = risk_percent
        self._risk_amount = risk_amount
        self._max_slippage_allowed = max_slippage_allowed

        # Behavioral
        self._selected_checklist = selected_checklist or []
        self._probability_bucket = probability_bucket
        self._discipline_mode_enabled = bool(discipline_mode_enabled)
        self._mandatory_checklist = mandatory_checklist or []
        self._confidence_score = confidence_score
        self._emotion_tag = emotion_tag

        # Environment
        self._volatility_regime = volatility_regime
        self._equity_snapshot = equity_snapshot
        self._drawdown_snapshot = drawdown_snapshot
        self._open_positions_count = open_positions_count
        self._correlation_exposure_snapshot = correlation_exposure_snapshot or {}

        # Governance
        self._violations_detected: List[str] = []
        self._strict_mode = strict_mode
        self._approved: Optional[bool] = None
        self._rejection_reason: Optional[str] = None

        # System
        self._metadata = metadata or {}
        self._finalized = False

    # =====================================================
    # VALIDATION UTILITIES
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ExecutionEventValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_positive(self, value: float, field: str) -> float:
        if not isinstance(value, (int, float)) or value <= 0:
            raise ExecutionEventValidationError(f"{field} must be positive")
        return float(value)

    def _validate_side(self, side: str) -> str:
        side = side.lower()
        if side not in ("buy", "sell"):
            raise ExecutionEventValidationError("side must be 'buy' or 'sell'")
        return side

    # =====================================================
    # GOVERNANCE METHODS
    # =====================================================

    def add_violation(self, violation: str):
        if not violation:
            return
        self._violations_detected.append(str(violation))

    def approve(self):
        if self._finalized:
            raise ExecutionEventValidationError("Event already finalized")
        self._approved = True
        self._finalized = True

    def reject(self, reason: str):
        if self._finalized:
            raise ExecutionEventValidationError("Event already finalized")
        self._approved = False
        self._rejection_reason = reason
        self._finalized = True

    # =====================================================
    # STATE INSPECTION
    # =====================================================

    @property
    def is_approved(self) -> Optional[bool]:
        return self._approved

    @property
    def strict_mode(self) -> bool:
        return self._strict_mode

    @property
    def violations(self) -> List[str]:
        return list(self._violations_detected)

    @property
    def is_finalized(self) -> bool:
        return self._finalized

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    # =====================================================
    # EXPORT FOR DISCIPLINE / DECISIONS
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:

        return {
            "event_id": self._event_id,
            "created_at": self._created_at,
            "event_type": self._event_type,
            "timestamp": self._timestamp,
            "account_id": self._account_id,
            "broker_id": self._broker_id,
            "symbol": self._symbol,
            "market_type": self._market_type,
            "side": self._side,
            "strategy_tag": self._strategy_tag,
            "setup_name": self._setup_name,
            "intended_entry_price": self._intended_entry_price,
            "intended_stop_loss": self._intended_stop_loss,
            "intended_target": self._intended_target,
            "intended_quantity": self._intended_quantity,
            "intended_lot_size": self._intended_lot_size,
            "intended_leverage": self._intended_leverage,
            "risk_percent": self._risk_percent,
            "risk_amount": self._risk_amount,
            "max_slippage_allowed": self._max_slippage_allowed,
            "selected_checklist": self._selected_checklist,
            "probability_bucket": self._probability_bucket,
            "discipline_mode_enabled": self._discipline_mode_enabled,
            "mandatory_checklist": self._mandatory_checklist,
            "confidence_score": self._confidence_score,
            "emotion_tag": self._emotion_tag,
            "volatility_regime": self._volatility_regime,
            "equity_snapshot": self._equity_snapshot,
            "drawdown_snapshot": self._drawdown_snapshot,
            "open_positions_count": self._open_positions_count,
            "correlation_exposure_snapshot": self._correlation_exposure_snapshot,
            "violations_detected": self._violations_detected,
            "strict_mode": self._strict_mode,
            "approved": self._approved,
            "rejection_reason": self._rejection_reason,
            "metadata": self._metadata,
            "finalized": self._finalized,
        }

    def __repr__(self):
        state = "APPROVED" if self._approved else "REJECTED" if self._approved is False else "PENDING"
        return f"<ExecutionEvent {self._event_id[:8]} {self._symbol} {state}>"
