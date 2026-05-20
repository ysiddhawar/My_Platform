from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from models.discipline_capture import DisciplineCapture


class TradeValidationError(Exception):
    pass


class Trade:
    """
    Institutional Forensic-Grade Trade Snapshot

    Captures:
    - Decision context
    - Risk state
    - Market state
    - Behavioral state
    - Economic outcome
    - Full execution metadata

    Compatible with:
    - core/evaluator.py
    - discipline layer
    - decisions layer
    - AI interpretation layer
    """

    __slots__ = (
        # Identity
        "_trade_id",
        "_account_id",
        "_broker_id",

        # Instrument
        "_symbol",
        "_market_type",
        "_side",

        # Strategy & Setup
        "_strategy_tag",
        "_setup_name",

        # Entry Snapshot
        "_entry_price",
        "_entry_time",
        "_entry_date",
        "_entry_day_of_week",
        "_entry_timezone",
        "_entry_spread",
        "_slippage_at_entry",
        "_stop_loss_at_entry",
        "_target_at_entry",

        # Exit Snapshot
        "_exit_price",
        "_exit_time",
        "_exit_date",
        "_exit_day_of_week",
        "_exit_reason",
        "_slippage_at_exit",

        # Trade Economics
        "_quantity",
        "_lot_size",
        "_contract_size",
        "_leverage_used",
        "_fees",
        "_commission",
        "_swaps",
        "_slippage_cost",
        "_gross_pnl",
        "_net_pnl",
        "_risk_amount",
        "_rrr_at_entry",
        "_r_multiple",

        # Behavioral
        "_checklist_before",
        "_checklist_after",
        "_confidence_score",
        "_emotion_tag",
        "_rule_violations_snapshot",
        "_probability_bucket",
        "_pre_trade_capture",
        "_post_trade_capture",
        "_line_history",
        "_minimum_target_price",
        "_minimum_target_reward",
        "_close_classification",
        "_closed_before_plan",
        "_notes",

        # Environment Snapshot
        "_volatility_regime_at_entry",
        "_equity_at_entry",
        "_drawdown_at_entry",
        "_open_positions_count",
        "_correlation_exposure_snapshot",

        # System
        "_metadata",
        "_is_closed",
    )

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        account_id: str,
        broker_id: str,
        symbol: str,
        market_type: str,
        side: str,
        strategy_tag: str,
        setup_name: str,
        entry_price: float,
        quantity: float,
        lot_size: float,
        leverage_used: float,
        contract_size: float = 1.0,
        stop_loss_at_entry: Optional[float] = None,
        target_at_entry: Optional[float] = None,
        entry_spread: float = 0.0,
        slippage_at_entry: float = 0.0,
        fees: float = 0.0,
        commission: float = 0.0,
        swaps: float = 0.0,
        entry_time: Optional[datetime] = None,
        checklist_before: Optional[List[str]] = None,
        probability_bucket: Optional[str] = None,
        confidence_score: Optional[float] = None,
        emotion_tag: Optional[str] = None,
        rule_violations_snapshot: Optional[List[str]] = None,
        pre_trade_capture: Optional[Dict[str, Any]] = None,
        post_trade_capture: Optional[Dict[str, Any]] = None,
        line_history: Optional[List[Dict[str, Any]]] = None,
        minimum_target_price: Optional[float] = None,
        minimum_target_reward: Optional[float] = None,
        close_classification: Optional[str] = None,
        closed_before_plan: bool = False,
        notes: Optional[str] = None,
        volatility_regime_at_entry: Optional[str] = None,
        equity_at_entry: Optional[float] = None,
        drawdown_at_entry: Optional[float] = None,
        open_positions_count: Optional[int] = None,
        correlation_exposure_snapshot: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        # Identity
        self._trade_id = str(uuid.uuid4())
        self._account_id = self._validate_non_empty(account_id, "account_id")
        self._broker_id = self._validate_non_empty(broker_id, "broker_id")

        # Instrument
        self._symbol = self._validate_non_empty(symbol, "symbol")
        self._market_type = self._validate_non_empty(market_type, "market_type")
        self._side = self._validate_side(side)

        # Strategy
        self._strategy_tag = strategy_tag.strip() if isinstance(strategy_tag, str) else ""
        self._setup_name = setup_name.strip() if isinstance(setup_name, str) else ""

        # Entry
        self._entry_price = self._validate_positive(entry_price, "entry_price")
        self._quantity = self._validate_positive(quantity, "quantity")
        self._lot_size = self._validate_positive(lot_size, "lot_size")
        self._contract_size = self._validate_positive(contract_size, "contract_size")
        self._leverage_used = self._validate_positive(leverage_used, "leverage_used")

        self._entry_time = entry_time or datetime.now(timezone.utc)
        self._entry_date = self._entry_time.date()
        self._entry_day_of_week = self._entry_time.strftime("%A")
        self._entry_timezone = str(self._entry_time.tzinfo)

        self._entry_spread = float(entry_spread)
        self._slippage_at_entry = float(slippage_at_entry)
        self._stop_loss_at_entry = stop_loss_at_entry
        self._target_at_entry = target_at_entry

        # Exit (initialized)
        self._exit_price = None
        self._exit_time = None
        self._exit_date = None
        self._exit_day_of_week = None
        self._exit_reason = None
        self._slippage_at_exit = 0.0

        # Economics
        self._fees = float(fees)
        self._commission = float(commission)
        self._swaps = float(swaps)
        self._slippage_cost = 0.0
        self._gross_pnl = None
        self._net_pnl = None
        self._risk_amount = None
        self._rrr_at_entry = None
        self._r_multiple = None

        # Behavioral
        self._checklist_before = checklist_before or []
        self._probability_bucket = probability_bucket
        self._checklist_after: List[str] = []
        self._confidence_score = confidence_score
        self._emotion_tag = emotion_tag
        self._rule_violations_snapshot = rule_violations_snapshot or []
        self._pre_trade_capture = dict(pre_trade_capture or {})
        self._post_trade_capture = dict(post_trade_capture or {})
        self._line_history = list(line_history or [])
        self._minimum_target_price = minimum_target_price
        self._minimum_target_reward = minimum_target_reward
        self._close_classification = close_classification
        self._closed_before_plan = bool(closed_before_plan)
        self._notes = notes

        # Environment
        self._volatility_regime_at_entry = volatility_regime_at_entry
        self._equity_at_entry = equity_at_entry
        self._drawdown_at_entry = drawdown_at_entry
        self._open_positions_count = open_positions_count
        self._correlation_exposure_snapshot = correlation_exposure_snapshot or {}

        # System
        self._metadata = metadata or {}
        self._is_closed = False

        self._compute_planned_metrics()

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise TradeValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_positive(self, value: float, field: str) -> float:
        if not isinstance(value, (int, float)) or value <= 0:
            raise TradeValidationError(f"{field} must be positive")
        return float(value)

    def _validate_side(self, side: str) -> str:
        side = side.lower()
        if side not in ("buy", "sell"):
            raise TradeValidationError("side must be 'buy' or 'sell'")
        return side

    # =====================================================
    # RISK METRICS
    # =====================================================

    def _compute_planned_metrics(self):
        self._risk_amount = None
        self._rrr_at_entry = None
        if self._stop_loss_at_entry is not None:
            risk_per_unit = abs(self._entry_price - self._stop_loss_at_entry)
            self._risk_amount = risk_per_unit * self._quantity * self._lot_size * self._contract_size

        if self._stop_loss_at_entry and self._target_at_entry:
            reward = abs(self._target_at_entry - self._entry_price)
            risk = abs(self._entry_price - self._stop_loss_at_entry)
            if risk > 0:
                self._rrr_at_entry = reward / risk

    # =====================================================
    # CLOSE TRADE
    # =====================================================

    def close(
        self,
        exit_price: float,
        exit_reason: str,
        slippage_at_exit: float = 0.0,
        checklist_after: Optional[List[str]] = None,
        probability_bucket: Optional[str] = None,
        post_trade_capture: Optional[Dict[str, Any]] = None,
        close_classification: Optional[str] = None,
        notes: Optional[str] = None,
        exit_time: Optional[datetime] = None,
    ):

        if self._is_closed:
            raise TradeValidationError("Trade already closed")

        self._exit_price = self._validate_positive(exit_price, "exit_price")
        self._exit_reason = exit_reason
        self._slippage_at_exit = float(slippage_at_exit)

        self._exit_time = exit_time or datetime.now(timezone.utc)
        self._exit_date = self._exit_time.date()
        self._exit_day_of_week = self._exit_time.strftime("%A")

        self._checklist_after: List[str] = checklist_after or []
        if probability_bucket is not None:
            self._probability_bucket = probability_bucket
        if post_trade_capture:
            self._post_trade_capture = dict(post_trade_capture)
        self._close_classification = close_classification or self._classify_close(exit_reason)
        self._closed_before_plan = self._is_closed_before_plan(exit_price)
        if notes:
            self._notes = notes

        self._compute_pnl()
        self._compute_r_multiple()

        self._is_closed = True

    # =====================================================
    # PNL
    # =====================================================

    def _compute_pnl(self):

        direction = 1 if self._side == "buy" else -1
        self._gross_pnl = direction * (
            (self._exit_price - self._entry_price) * self._quantity * self._lot_size * self._contract_size
        )

        # MT5 DEAL_PROFIT = price_pnl + commission + swaps
        # where commission and swaps are negative for costs.
        # The fill prices already embed any slippage, so no separate slippage deduction.
        self._slippage_cost = self._slippage_at_entry + self._slippage_at_exit
        self._net_pnl = self._gross_pnl + self._commission + self._swaps

    def _compute_r_multiple(self):
        if self._risk_amount and self._risk_amount != 0:
            self._r_multiple = self._net_pnl / self._risk_amount

    @property
    def trade_id(self) -> str:
        return self._trade_id

    def _classify_close(self, exit_reason: str) -> str:
        normalized = str(exit_reason or "").lower()
        if normalized in {"target", "take_profit", "target_hit"}:
            return "target_hit"
        if normalized in {"stop", "stop_loss", "stop_hit"}:
            return "stop_hit"
        if normalized:
            return "manual_exit"
        return "unknown"

    def _is_closed_before_plan(self, exit_price: float) -> bool:
        if self._target_at_entry is None or self._stop_loss_at_entry is None:
            return False
        planned_prices = {round(float(self._target_at_entry), 8), round(float(self._stop_loss_at_entry), 8)}
        return round(float(exit_price), 8) not in planned_prices

    def close_trade(
        self,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        exit_reason: str = "",
        slippage_at_exit: float = 0.0,
        checklist_after: Optional[List[str]] = None,
        probability_bucket: Optional[str] = None,
        post_trade_capture: Optional[Dict[str, Any]] = None,
        close_classification: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        coerced_exit_time = self._coerce_datetime(exit_time)
        self.close(
            exit_price=exit_price,
            exit_reason=exit_reason,
            slippage_at_exit=slippage_at_exit,
            checklist_after=checklist_after,
            probability_bucket=probability_bucket,
            post_trade_capture=post_trade_capture,
            close_classification=close_classification,
            notes=notes,
            exit_time=coerced_exit_time,
        )

    def add_line_snapshot(self, snapshot: Dict[str, Any]):
        if not isinstance(snapshot, dict):
            raise TradeValidationError("line snapshot must be dict")
        self._line_history.append(dict(snapshot))

    def append_notes(self, notes: str):
        if not notes:
            return
        self._notes = notes if not self._notes else f"{self._notes}\n{notes}"

    def record_lifecycle_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        line_snapshot: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ):
        if line_snapshot:
            self.add_line_snapshot(line_snapshot)
        if notes:
            self.append_notes(notes)
        if metadata_update:
            self._metadata.update(dict(metadata_update))
        timestamp = datetime.now(timezone.utc).isoformat()
        lifecycle_events = list(self._metadata.get("lifecycle_events") or [])
        lifecycle_events.append(
            {
                "type": event_type,
                "timestamp": timestamp,
                "payload": dict(payload or {}),
            }
        )
        self._metadata["lifecycle_events"] = lifecycle_events
        self._metadata["last_broker_sync_at"] = timestamp
        self._metadata["last_broker_event_type"] = event_type

    def update_position_plan(
        self,
        stop_loss_at_entry: Optional[float] = None,
        target_at_entry: Optional[float] = None,
        minimum_target_price: Optional[float] = None,
        minimum_target_reward: Optional[float] = None,
        line_snapshot: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
        event_type: str = "POSITION_MODIFIED",
    ):
        if self._is_closed:
            raise TradeValidationError("Cannot modify a closed trade")
        if stop_loss_at_entry is not None:
            self._stop_loss_at_entry = float(stop_loss_at_entry)
        if target_at_entry is not None:
            self._target_at_entry = float(target_at_entry)
        if minimum_target_price is not None:
            self._minimum_target_price = float(minimum_target_price)
        if minimum_target_reward is not None:
            self._minimum_target_reward = float(minimum_target_reward)
        self._compute_planned_metrics()
        self.record_lifecycle_event(
            event_type=event_type,
            payload={
                "stop_loss_at_entry": self._stop_loss_at_entry,
                "target_at_entry": self._target_at_entry,
                "minimum_target_price": self._minimum_target_price,
            },
            line_snapshot=line_snapshot,
            notes=notes,
            metadata_update=metadata_update,
        )

    def scale_in(
        self,
        additional_quantity: float,
        fill_price: float,
        fees: float = 0.0,
        commission: float = 0.0,
        swaps: float = 0.0,
        slippage_at_entry: float = 0.0,
        line_snapshot: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ):
        if self._is_closed:
            raise TradeValidationError("Cannot scale into a closed trade")
        additional_quantity = self._validate_positive(additional_quantity, "additional_quantity")
        fill_price = self._validate_positive(fill_price, "fill_price")
        total_quantity = self._quantity + additional_quantity
        self._entry_price = ((self._entry_price * self._quantity) + (fill_price * additional_quantity)) / total_quantity
        self._quantity = total_quantity
        self._fees += float(fees)
        self._commission += float(commission)
        self._swaps += float(swaps)
        self._slippage_at_entry += float(slippage_at_entry)
        self._compute_planned_metrics()
        self.record_lifecycle_event(
            event_type="SCALE_IN",
            payload={
                "additional_quantity": additional_quantity,
                "fill_price": fill_price,
                "new_quantity": self._quantity,
                "new_entry_price": self._entry_price,
            },
            line_snapshot=line_snapshot,
            notes=notes,
            metadata_update=metadata_update,
        )

    def create_partial_close_trade(
        self,
        closed_quantity: float,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        exit_reason: str = "",
        slippage_at_exit: float = 0.0,
        checklist_after: Optional[List[str]] = None,
        probability_bucket: Optional[str] = None,
        post_trade_capture: Optional[Dict[str, Any]] = None,
        close_classification: Optional[str] = None,
        notes: Optional[str] = None,
        line_snapshot: Optional[Dict[str, Any]] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
        partial_trade_id: Optional[str] = None,
    ) -> "Trade":
        if self._is_closed:
            raise TradeValidationError("Cannot partially close a closed trade")
        closed_quantity = self._validate_positive(closed_quantity, "closed_quantity")
        if closed_quantity >= self._quantity:
            raise TradeValidationError("closed_quantity must be smaller than current quantity for partial close")

        existing_quantity = self._quantity
        proportion = closed_quantity / existing_quantity
        child_payload = self.to_dict()
        child_payload.update(
            {
                "trade_id": partial_trade_id or str(uuid.uuid4()),
                "quantity": closed_quantity,
                "fees": self._fees * proportion,
                "commission": self._commission * proportion,
                "swaps": self._swaps * proportion,
                "slippage_at_entry": self._slippage_at_entry * proportion,
                "metadata": {
                    **dict(self._metadata or {}),
                    "parent_trade_id": self._trade_id,
                    "is_partial_close_slice": True,
                },
            }
        )
        child_trade = Trade.from_dict(child_payload)
        child_trade.close_trade(
            exit_price=exit_price,
            exit_time=exit_time,
            exit_reason=exit_reason,
            slippage_at_exit=slippage_at_exit,
            checklist_after=checklist_after,
            probability_bucket=probability_bucket,
            post_trade_capture=post_trade_capture,
            close_classification=close_classification,
            notes=notes,
        )

        self._quantity = existing_quantity - closed_quantity
        self._fees -= self._fees * proportion
        self._commission -= self._commission * proportion
        self._swaps -= self._swaps * proportion
        self._slippage_at_entry -= self._slippage_at_entry * proportion
        self._compute_planned_metrics()
        self.record_lifecycle_event(
            event_type="PARTIAL_CLOSE",
            payload={
                "closed_quantity": closed_quantity,
                "remaining_quantity": self._quantity,
                "partial_trade_id": child_trade.trade_id,
                "exit_price": exit_price,
            },
            line_snapshot=line_snapshot,
            notes=notes,
            metadata_update=metadata_update,
        )
        return child_trade

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Trade":
        if not isinstance(payload, dict):
            raise TradeValidationError("payload must be dict")

        trade = cls(
            account_id=payload["account_id"],
            broker_id=payload.get("broker_id", "BROKER"),
            symbol=payload["symbol"],
            market_type=payload.get("market_type", "stock"),
            side=payload["side"],
            strategy_tag=payload.get("strategy_tag") or payload.get("strategy") or "",
            setup_name=payload.get("setup_name") or "",
            entry_price=payload["entry_price"],
            quantity=payload["quantity"],
            lot_size=payload.get("lot_size", 1.0),
            contract_size=payload.get("contract_size", 1.0),
            leverage_used=payload.get("leverage_used", 1.0),
            stop_loss_at_entry=payload.get("stop_loss_at_entry"),
            target_at_entry=payload.get("target_at_entry"),
            entry_spread=payload.get("entry_spread", 0.0),
            slippage_at_entry=payload.get("slippage_at_entry", 0.0),
            fees=payload.get("fees", 0.0),
            commission=payload.get("commission", 0.0),
            swaps=payload.get("swaps", 0.0),
            checklist_before=payload.get("checklist_before"),
            probability_bucket=payload.get("probability_bucket"),
            confidence_score=payload.get("confidence_score"),
            emotion_tag=payload.get("emotion_tag"),
            rule_violations_snapshot=payload.get("rule_violations_snapshot"),
            pre_trade_capture=payload.get("pre_trade_capture"),
            post_trade_capture=payload.get("post_trade_capture"),
            line_history=payload.get("line_history"),
            minimum_target_price=payload.get("minimum_target_price"),
            minimum_target_reward=payload.get("minimum_target_reward"),
            close_classification=payload.get("close_classification"),
            closed_before_plan=payload.get("closed_before_plan", False),
            notes=payload.get("notes"),
            metadata=payload.get("metadata"),
            volatility_regime_at_entry=payload.get("volatility_regime_at_entry"),
            equity_at_entry=payload.get("equity_at_entry"),
            drawdown_at_entry=payload.get("drawdown_at_entry"),
            open_positions_count=payload.get("open_positions_count"),
            correlation_exposure_snapshot=payload.get("correlation_exposure_snapshot"),
        )
        if payload.get("trade_id"):
            trade._trade_id = payload["trade_id"]
        if payload.get("entry_time"):
            trade._entry_time = cls._coerce_datetime(payload["entry_time"])
            trade._entry_date = trade._entry_time.date()
            trade._entry_day_of_week = trade._entry_time.strftime("%A")
            trade._entry_timezone = str(trade._entry_time.tzinfo)
        if payload.get("is_closed"):
            trade.close(
                exit_price=payload["exit_price"],
                exit_reason=payload.get("exit_reason", ""),
                slippage_at_exit=payload.get("slippage_at_exit", 0.0),
                checklist_after=payload.get("checklist_after"),
                probability_bucket=payload.get("probability_bucket"),
                post_trade_capture=payload.get("post_trade_capture"),
                close_classification=payload.get("close_classification"),
                notes=payload.get("notes"),
                exit_time=cls._coerce_datetime(payload.get("exit_time")),
            )
        return trade

    @staticmethod
    def _coerce_datetime(value: Any) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                pass
            for pattern in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(normalized, pattern).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            raise TradeValidationError(f"Invalid datetime value: {value}")
        raise TradeValidationError("Invalid datetime value")

    # =====================================================
    # EXPORT
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:
        total_cost = self._fees + self._commission + self._swaps + self._slippage_cost
        entry_hour = self._entry_time.hour
        exit_hour = self._exit_time.hour if self._exit_time else None

        return {
            # System
            "trade_id": self._trade_id,
            "account_id": self._account_id,
            "broker_id": self._broker_id,
            "symbol": self._symbol,
            "market_type": self._market_type,
            "side": self._side,
            "is_closed": self._is_closed,
            "metadata": self._metadata,

            # Strategy
            "strategy": self._strategy_tag,
            "setup_name": self._setup_name,

            # Entry
            "entry_price": self._entry_price,
            "entry_time": self._entry_time,
            "entry_date": self._entry_date,
            "entry_day_of_week": self._entry_day_of_week,
            "entry_timezone": self._entry_timezone,
            "entry_hour": entry_hour,
            "entry_hour_bucket": f"{entry_hour:02d}:00-{(entry_hour + 1) % 24:02d}:00",
            "entry_spread": self._entry_spread,
            "slippage_at_entry": self._slippage_at_entry,
            "stop_loss_at_entry": self._stop_loss_at_entry,
            "target_at_entry": self._target_at_entry,

            # Exit
            "exit_price": self._exit_price,
            "exit_time": self._exit_time,
            "exit_date": self._exit_date,
            "exit_day_of_week": self._exit_day_of_week,
            "exit_hour": exit_hour,
            "exit_hour_bucket": (
                f"{exit_hour:02d}:00-{(exit_hour + 1) % 24:02d}:00"
                if exit_hour is not None
                else None
            ),
            "exit_reason": self._exit_reason,
            "slippage_at_exit": self._slippage_at_exit,

            # Economics
            "quantity": self._quantity,
            "lot_size": self._lot_size,
            "leverage_used": self._leverage_used,
            "gross_pnl": self._gross_pnl,
            "net_pnl": self._net_pnl,
            "fees": self._fees,
            "commission": self._commission,
            "swaps": self._swaps,
            "slippage_cost": self._slippage_cost,
            "total_cost": total_cost,
            "risk_amount": self._risk_amount,
            "rrr_at_entry": self._rrr_at_entry,
            "r_multiple": self._r_multiple,

            # Behavioral
            "checklist_before": self._checklist_before,
            "checklist_after": self._checklist_after,
            "probability_bucket": self._probability_bucket,
            "confidence_score": self._confidence_score,
            "emotion_tag": self._emotion_tag,
            "rule_violations_snapshot": self._rule_violations_snapshot,
            "pre_trade_capture": self._pre_trade_capture,
            "post_trade_capture": self._post_trade_capture,
            "line_history": self._line_history,
            "minimum_target_price": self._minimum_target_price,
            "minimum_target_reward": self._minimum_target_reward,
            "close_classification": self._close_classification,
            "closed_before_plan": self._closed_before_plan,
            "notes": self._notes,

            # Environment
            "volatility_regime_at_entry": self._volatility_regime_at_entry,
            "equity_at_entry": self._equity_at_entry,
            "drawdown_at_entry": self._drawdown_at_entry,
            "open_positions_count": self._open_positions_count,
            "correlation_exposure_snapshot": self._correlation_exposure_snapshot,
            "entry_details": {
                "entry_price": self._entry_price,
                "entry_time": self._entry_time.isoformat(),
                "stop_loss_at_entry": self._stop_loss_at_entry,
                "target_at_entry": self._target_at_entry,
                "quantity": self._quantity,
                "lot_size": self._lot_size,
                "contract_size": self._contract_size,
                "leverage_used": self._leverage_used,
                "minimum_target_price": self._minimum_target_price,
            },
            "exit_details": {
                "exit_price": self._exit_price,
                "exit_time": self._exit_time.isoformat() if self._exit_time else None,
                "exit_reason": self._exit_reason,
                "close_classification": self._close_classification,
                "closed_before_plan": self._closed_before_plan,
            } if self._exit_time else None,
            "economics": {
                "gross_pnl": self._gross_pnl,
                "net_pnl": self._net_pnl,
                "fees": self._fees,
                "commission": self._commission,
                "swaps": self._swaps,
                "slippage_cost": self._slippage_cost,
                "total_cost": total_cost,
                "risk_amount": self._risk_amount,
                "rrr_at_entry": self._rrr_at_entry,
                "r_multiple": self._r_multiple,
                "required_reward_for_min_target": self._minimum_target_reward,
            },
            "behavioral": {
                "checklist_before": self._checklist_before,
                "checklist_after": self._checklist_after,
                "probability_bucket": self._probability_bucket,
                "confidence_score": self._confidence_score,
                "emotion_tag": self._emotion_tag,
                "rule_violations_snapshot": self._rule_violations_snapshot,
                "pre_trade_capture": self._pre_trade_capture,
                "post_trade_capture": self._post_trade_capture,
                "line_history": self._line_history,
                "notes": self._notes,
            },
            "environment": {
                "volatility_regime_at_entry": self._volatility_regime_at_entry,
                "equity_at_entry": self._equity_at_entry,
                "drawdown_at_entry": self._drawdown_at_entry,
                "open_positions_count": self._open_positions_count,
                "correlation_exposure_snapshot": self._correlation_exposure_snapshot,
            },
            "system": {
                "metadata": self._metadata,
                "is_closed": self._is_closed,
            },
            "created_at": self._entry_time.isoformat(),
            "updated_at": (self._exit_time or self._entry_time).isoformat(),
        }

    def __repr__(self):
        status = "CLOSED" if self._is_closed else "OPEN"
        return (
            f"<Trade {self._trade_id[:8]} "
            f"{self._symbol} {self._side.upper()} "
            f"{status}>"
        )
