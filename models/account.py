from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class AccountValidationError(Exception):
    pass


class Account:
    """
    Institutional-Grade Trading Account Model

    Responsibilities:
    - Capital state tracking
    - Risk governance enforcement
    - Level classification (Survival / Consistency / Profitable)
    - Drawdown monitoring
    - Exposure tracking
    - Multi-broker compatibility
    - Discipline + AI integration support
    """

    __slots__ = (
        # Identity
        "_account_id",
        "_broker_id",
        "_account_name",
        "_created_at",
        "_updated_at",
        "_base_currency",
        "_supported_market_types",

        # Capital State
        "_initial_balance",
        "_current_balance",
        "_equity",
        "_max_equity",
        "_drawdown",
        "_max_drawdown",

        # Risk Governance
        "_risk_level",  # survival / consistency / profitable
        "_allowed_risk_percent",
        "_max_leverage_allowed",
        "_capital_throttle_percent",

        # Exposure
        "_open_positions_count",
        "_strategy_exposure",
        "_correlation_exposure",

        # Status
        "_is_active",
        "_metadata",
    )

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        broker_id: str,
        account_name: str,
        initial_balance: float,
        risk_level: str = "survival",
        allowed_risk_percent: float = 0.25,
        max_leverage_allowed: float = 10.0,
        capital_throttle_percent: float = 100.0,
        base_currency: str = "USD",
        supported_market_types: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self._account_id = str(uuid.uuid4())
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at

        self._broker_id = self._validate_non_empty(broker_id, "broker_id")
        self._account_name = self._validate_non_empty(account_name, "account_name")
        self._base_currency = self._validate_non_empty(base_currency, "base_currency")
        self._supported_market_types = self._validate_market_types(
            supported_market_types or ["stock", "forex", "crypto", "futures", "options"]
        )

        self._initial_balance = self._validate_positive(
            initial_balance, "initial_balance"
        )
        self._current_balance = self._initial_balance
        self._equity = self._initial_balance
        self._max_equity = self._initial_balance

        self._drawdown = 0.0
        self._max_drawdown = 0.0

        self._risk_level = self._validate_risk_level(risk_level)
        self._allowed_risk_percent = self._validate_positive(
            allowed_risk_percent, "allowed_risk_percent"
        )
        self._max_leverage_allowed = self._validate_positive(
            max_leverage_allowed, "max_leverage_allowed"
        )
        self._capital_throttle_percent = self._validate_percentage(
            capital_throttle_percent, "capital_throttle_percent"
        )

        self._open_positions_count = 0
        self._strategy_exposure: Dict[str, float] = {}
        self._correlation_exposure: Dict[str, float] = {}

        self._is_active = True
        self._metadata = metadata or {}

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AccountValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_positive(self, value: float, field: str) -> float:
        if not isinstance(value, (int, float)) or value <= 0:
            raise AccountValidationError(f"{field} must be positive")
        return float(value)

    def _validate_percentage(self, value: float, field: str) -> float:
        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            raise AccountValidationError(f"{field} must be between 0 and 100")
        return float(value)

    def _validate_risk_level(self, level: str) -> str:
        level = level.lower()
        if level not in ("survival", "consistency", "profitable"):
            raise AccountValidationError(
                "risk_level must be: survival, consistency, or profitable"
            )
        return level

    def _validate_market_types(self, market_types: list[str]) -> list[str]:
        if not isinstance(market_types, list) or not market_types:
            raise AccountValidationError("supported_market_types must be non-empty list")
        cleaned = []
        for market in market_types:
            if not isinstance(market, str) or not market.strip():
                raise AccountValidationError("supported_market_types must contain non-empty strings")
            cleaned.append(market.strip().lower())
        return cleaned

    def _touch(self):
        self._updated_at = datetime.now(timezone.utc)

    # =====================================================
    # CAPITAL UPDATE
    # =====================================================

    def update_equity(self, new_equity: float):

        new_equity = self._validate_positive(new_equity, "new_equity")

        self._equity = new_equity
        self._current_balance = new_equity

        if new_equity > self._max_equity:
            self._max_equity = new_equity

        self._drawdown = (
            (self._max_equity - self._equity) / self._max_equity
            if self._max_equity > 0
            else 0.0
        )

        if self._drawdown > self._max_drawdown:
            self._max_drawdown = self._drawdown
        self._touch()

    # =====================================================
    # EXPOSURE TRACKING
    # =====================================================

    def increment_position(self, strategy_tag: str, exposure: float):
        self._open_positions_count += 1
        self._strategy_exposure[strategy_tag] = (
            self._strategy_exposure.get(strategy_tag, 0.0) + exposure
        )
        self._touch()

    def decrement_position(self, strategy_tag: str, exposure: float):
        self._open_positions_count = max(0, self._open_positions_count - 1)
        self._strategy_exposure[strategy_tag] = max(
            0.0,
            self._strategy_exposure.get(strategy_tag, 0.0) - exposure
        )
        self._touch()

    def update_correlation_exposure(self, exposure_map: Dict[str, float]):
        if not isinstance(exposure_map, dict):
            raise AccountValidationError("correlation_exposure must be dict")
        self._correlation_exposure = dict(exposure_map)
        self._touch()

    # =====================================================
    # GOVERNANCE ACCESSORS
    # =====================================================

    @property
    def allowed_risk_percent(self) -> float:
        return self._allowed_risk_percent

    @property
    def max_leverage_allowed(self) -> float:
        return self._max_leverage_allowed

    @property
    def risk_level(self) -> str:
        return self._risk_level

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def broker_id(self) -> str:
        return self._broker_id

    @property
    def account_name(self) -> str:
        return self._account_name

    @property
    def base_currency(self) -> str:
        return self._base_currency

    @property
    def supported_market_types(self) -> list[str]:
        return list(self._supported_market_types)

    @property
    def drawdown(self) -> float:
        return self._drawdown

    @property
    def max_drawdown(self) -> float:
        return self._max_drawdown

    @property
    def equity(self) -> float:
        return self._equity

    @property
    def is_active(self) -> bool:
        return self._is_active

    # =====================================================
    # ACTIVATION CONTROL
    # =====================================================

    def deactivate(self):
        self._is_active = False
        self._touch()

    def activate(self):
        self._is_active = True
        self._touch()

    # =====================================================
    # EXPORT
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self._account_id,
            "broker_id": self._broker_id,
            "account_name": self._account_name,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "base_currency": self._base_currency,
            "supported_market_types": self._supported_market_types,
            "initial_balance": self._initial_balance,
            "current_balance": self._current_balance,
            "equity": self._equity,
            "max_equity": self._max_equity,
            "drawdown": self._drawdown,
            "max_drawdown": self._max_drawdown,
            "risk_level": self._risk_level,
            "allowed_risk_percent": self._allowed_risk_percent,
            "max_leverage_allowed": self._max_leverage_allowed,
            "capital_throttle_percent": self._capital_throttle_percent,
            "governance_tier": self._risk_level,
            "open_positions_count": self._open_positions_count,
            "strategy_exposure": self._strategy_exposure,
            "correlation_exposure": self._correlation_exposure,
            "is_active": self._is_active,
            "metadata": self._metadata,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Account":
        if not isinstance(payload, dict):
            raise AccountValidationError("payload must be dict")

        account = cls(
            broker_id=payload["broker_id"],
            account_name=payload["account_name"],
            initial_balance=payload["initial_balance"],
            risk_level=payload.get("risk_level") or payload.get("governance_tier", "survival"),
            allowed_risk_percent=payload.get("allowed_risk_percent", 0.25),
            max_leverage_allowed=payload.get("max_leverage_allowed", 10.0),
            capital_throttle_percent=payload.get("capital_throttle_percent", 100.0),
            base_currency=payload.get("base_currency", "USD"),
            supported_market_types=payload.get("supported_market_types"),
            metadata=payload.get("metadata"),
        )
        account._account_id = payload.get("account_id", account._account_id)
        account._created_at = cls._coerce_datetime(payload.get("created_at")) or account._created_at
        account._updated_at = cls._coerce_datetime(payload.get("updated_at")) or account._created_at
        account._current_balance = float(payload.get("current_balance", account._current_balance))
        account._equity = float(payload.get("equity", account._equity))
        account._max_equity = float(payload.get("max_equity", account._max_equity))
        account._drawdown = float(payload.get("drawdown", account._drawdown))
        account._max_drawdown = float(payload.get("max_drawdown", account._max_drawdown))
        account._open_positions_count = int(payload.get("open_positions_count", account._open_positions_count))
        account._strategy_exposure = dict(payload.get("strategy_exposure", {}))
        account._correlation_exposure = dict(payload.get("correlation_exposure", {}))
        account._is_active = bool(payload.get("is_active", account._is_active))
        return account

    @staticmethod
    def _coerce_datetime(value: Any) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise AccountValidationError("Invalid datetime value")

    def __repr__(self):
        return (
            f"<Account {self._account_name} "
            f"Level={self._risk_level} "
            f"Equity={self._equity:.2f}>"
        )
