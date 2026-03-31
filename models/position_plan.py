from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PositionPlan:
    quantity: float
    risk_amount: float
    reward_amount: float
    required_capital: float
    estimated_fees: float
    estimated_slippage: float
    estimated_total_cost: float
    minimum_target_price: Optional[float]
    minimum_target_reward: Optional[float]
    entry_price: float
    stop_loss_price: float
    target_price: Optional[float]
    market_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quantity": self.quantity,
            "risk_amount": self.risk_amount,
            "reward_amount": self.reward_amount,
            "required_capital": self.required_capital,
            "estimated_fees": self.estimated_fees,
            "estimated_slippage": self.estimated_slippage,
            "estimated_total_cost": self.estimated_total_cost,
            "minimum_target_price": self.minimum_target_price,
            "minimum_target_reward": self.minimum_target_reward,
            "entry_price": self.entry_price,
            "stop_loss_price": self.stop_loss_price,
            "target_price": self.target_price,
            "market_type": self.market_type,
            "metadata": dict(self.metadata),
        }
