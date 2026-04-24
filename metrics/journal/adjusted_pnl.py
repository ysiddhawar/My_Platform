import numpy as np
from core.registry import registry


def _resolve_gross(context):
    gross = np.asarray(
        context.data.get("gross_pnl", []),
        dtype=np.float64
    )
    if gross.size == 0:
        gross = np.asarray(
            context.data.get("returns", []),
            dtype=np.float64
        )
    return gross[~np.isnan(gross)]


def _resolve_cost_array(values, size):
    arr = np.asarray(values if values is not None else [], dtype=np.float64)
    arr = np.nan_to_num(arr)

    if size == 0:
        return np.zeros(0, dtype=np.float64)
    if arr.size == 0:
        return np.zeros(size, dtype=np.float64)
    if arr.size == 1:
        return np.full(size, float(arr[0]), dtype=np.float64)
    if arr.size != size:
        return np.resize(arr, size)
    return arr


def adjusted_pnl(context):

    gross = _resolve_gross(context)

    if gross.size == 0:
        return None

    brokerage = _resolve_cost_array(
        context.data.get("brokerage"),
        gross.size
    )
    slippage = _resolve_cost_array(
        context.data.get("slippage"),
        gross.size
    )
    swaps = _resolve_cost_array(
        context.data.get("swaps"),
        gross.size
    )

    total_cost = brokerage + slippage + swaps
    net = gross - total_cost
    capital = float(context.data.get("capital") or context.data.get("total_capital") or 100000.0)
    if capital <= 0:
        capital = 100000.0

    net_returns = np.divide(net, capital, dtype=np.float64)
    net_returns = net_returns[np.isfinite(net_returns)]
    net_returns = np.clip(net_returns, -0.999, 10.0)

    cumulative_net = np.cumsum(net)

    total_gross = np.sum(gross)
    total_net = np.sum(net)

    impact = (
        (total_gross - total_net) / total_gross
        if total_gross != 0 else None
    )

    # -----------------------------------------
    # Write downstream research returns
    # -----------------------------------------
    context.set_cache("net_returns", net_returns)
    context.set_cache("net_pnl_series", net)

    return {
        "total_gross_pnl": float(total_gross),
        "total_net_pnl": float(total_net),
        "cost_impact_ratio": float(impact) if impact else None,
        "cumulative_net_curve": cumulative_net.tolist()
    }


registry.register(
    "adjusted_pnl",
    adjusted_pnl,
    category="journal",
    dependencies=["cost_summary"]
)
