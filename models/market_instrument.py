from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class MarketInstrument:
    symbol: str
    market_type: str
    contract_multiplier: float = 1.0
    price_increment: float = 0.01
    base_fee_rate: float = 0.0
    base_slippage_rate: float = 0.0
    margin_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "market_type": self.market_type,
            "contract_multiplier": self.contract_multiplier,
            "price_increment": self.price_increment,
            "base_fee_rate": self.base_fee_rate,
            "base_slippage_rate": self.base_slippage_rate,
            "margin_rate": self.margin_rate,
            "metadata": dict(self.metadata),
        }
