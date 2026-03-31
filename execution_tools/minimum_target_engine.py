from __future__ import annotations

from typing import Dict, Optional


class MinimumTargetEngine:
    PROBABILITY_TO_R = {
        "<40%": 2.5,
        "40%": 2.0,
        "50%": 1.5,
        "60%": 1.0,
        ">60%": 0.8,
    }

    def get_required_reward(
        self,
        probability_bucket: Optional[str],
        risk_amount: float,
        total_costs: float,
    ) -> Optional[float]:
        if not probability_bucket:
            return None
        multiplier = self.PROBABILITY_TO_R.get(probability_bucket)
        if multiplier is None:
            return None
        return round((risk_amount * multiplier) + total_costs, 6)

    def get_minimum_target_price(
        self,
        probability_bucket: Optional[str],
        entry_price: float,
        stop_loss_price: float,
        quantity: float,
        side: str,
        total_costs: float,
    ) -> Optional[float]:
        risk_amount = abs(entry_price - stop_loss_price) * quantity
        required_reward = self.get_required_reward(
            probability_bucket=probability_bucket,
            risk_amount=risk_amount,
            total_costs=total_costs,
        )
        if required_reward is None or quantity <= 0:
            return None
        reward_per_unit = required_reward / quantity
        direction = 1 if str(side).lower() == "buy" else -1
        return round(entry_price + (direction * reward_per_unit), 6)
