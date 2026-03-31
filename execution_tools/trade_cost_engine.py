from __future__ import annotations

from typing import Any, Dict, Optional

from models.market_instrument import MarketInstrument


class TradeCostEngine:
    def estimate_costs(
        self,
        entry_price: float,
        quantity: float,
        instrument: MarketInstrument,
        explicit_costs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        explicit_costs = explicit_costs or {}
        notional = abs(entry_price * quantity * instrument.contract_multiplier)
        brokerage = float(explicit_costs.get("brokerage", notional * instrument.base_fee_rate))
        slippage = float(explicit_costs.get("slippage", notional * instrument.base_slippage_rate))
        exchange_fees = float(explicit_costs.get("exchange_fees", 0.0))
        taxes = float(explicit_costs.get("taxes", 0.0))
        other = float(explicit_costs.get("other_charges", 0.0))
        total = brokerage + slippage + exchange_fees + taxes + other
        return {
            "brokerage": round(brokerage, 6),
            "slippage": round(slippage, 6),
            "exchange_fees": round(exchange_fees, 6),
            "taxes": round(taxes, 6),
            "other_charges": round(other, 6),
            "total": round(total, 6),
        }
