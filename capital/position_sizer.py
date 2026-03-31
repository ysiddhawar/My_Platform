import numpy as np
from core.registry import registry


def position_sizer(context):

    capital = context.data.get("capital")
    entry = context.data.get("entry_price")
    stop = context.data.get("stop_price")

    if capital is None or entry is None or stop is None:
        return None

    stop_dist = abs(entry - stop)
    if stop_dist == 0:
        return None

    risk_pct = context.data.get("risk_per_trade", 0.01)
    risk_amt = capital * risk_pct

    base_size = risk_amt / stop_dist

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    _, R = aligned
    vol = np.mean(np.std(R, axis=1))

    if vol > 0:
        base_size /= vol

    kelly_out = context.get_result("kelly")
    if kelly_out is not None:
        avg_k = np.mean(list(kelly_out.values()))
        base_size *= max(avg_k, 0)

    frag = context.get_result("portfolio_fragility_index")
    if frag is not None:
        base_size *= max(0.1, 1 - frag)

    return float(max(base_size, 0.0))


registry.register(
    "position_sizer",
    position_sizer,
    category="capital",
    dependencies=[
        "portfolio_preprocessor",
        "kelly",
        "portfolio_fragility_index"
    ]
)