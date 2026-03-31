from __future__ import annotations

from typing import Any, Dict, Optional

from models.market_instrument import MarketInstrument


class MarketSpecResolver:
    DEFAULTS: Dict[str, Dict[str, float]] = {
        "stock": {"contract_multiplier": 1.0, "base_fee_rate": 0.0005, "base_slippage_rate": 0.0003, "margin_rate": 1.0},
        "forex": {"contract_multiplier": 100000.0, "base_fee_rate": 0.00002, "base_slippage_rate": 0.00005, "margin_rate": 0.05},
        "crypto": {"contract_multiplier": 1.0, "base_fee_rate": 0.001, "base_slippage_rate": 0.0008, "margin_rate": 1.0},
        "futures": {"contract_multiplier": 1.0, "base_fee_rate": 0.0004, "base_slippage_rate": 0.0002, "margin_rate": 0.1},
        "options": {"contract_multiplier": 100.0, "base_fee_rate": 0.001, "base_slippage_rate": 0.0006, "margin_rate": 1.0},
    }

    def resolve(
        self,
        symbol: str,
        market_type: Optional[str],
        instrument_overrides: Optional[Dict[str, Any]] = None,
    ) -> MarketInstrument:
        normalized = (market_type or "stock").lower()
        template = dict(self.DEFAULTS.get(normalized, self.DEFAULTS["stock"]))
        instrument_overrides = instrument_overrides or {}
        template.update(
            {
                "contract_multiplier": float(instrument_overrides.get("contract_multiplier", template["contract_multiplier"])),
                "price_increment": float(instrument_overrides.get("price_increment", 0.01)),
                "base_fee_rate": float(instrument_overrides.get("base_fee_rate", template["base_fee_rate"])),
                "base_slippage_rate": float(instrument_overrides.get("base_slippage_rate", template["base_slippage_rate"])),
                "margin_rate": float(instrument_overrides.get("margin_rate", template["margin_rate"])),
            }
        )
        return MarketInstrument(
            symbol=symbol,
            market_type=normalized,
            contract_multiplier=template["contract_multiplier"],
            price_increment=template["price_increment"],
            base_fee_rate=template["base_fee_rate"],
            base_slippage_rate=template["base_slippage_rate"],
            margin_rate=template["margin_rate"],
            metadata={k: v for k, v in instrument_overrides.items() if k not in template},
        )
