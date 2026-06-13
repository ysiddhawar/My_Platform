from __future__ import annotations

from typing import Any


TRADE_OUTCOME_TOLERANCE = 0.001


def coerce_pnl(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def classify_trade_outcome(net_pnl: Any, is_closed: bool, tolerance: float = TRADE_OUTCOME_TOLERANCE) -> str:
    if not is_closed:
        return "open"
    pnl = coerce_pnl(net_pnl)
    if pnl > tolerance:
        return "win"
    if pnl < -tolerance:
        return "loss"
    return "breakeven"


def is_win(net_pnl: Any, is_closed: bool = True) -> bool:
    return classify_trade_outcome(net_pnl, is_closed) == "win"


def is_loss(net_pnl: Any, is_closed: bool = True) -> bool:
    return classify_trade_outcome(net_pnl, is_closed) == "loss"


def is_breakeven(net_pnl: Any, is_closed: bool = True) -> bool:
    return classify_trade_outcome(net_pnl, is_closed) == "breakeven"
