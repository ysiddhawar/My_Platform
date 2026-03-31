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


def _get_cost_arrays(context):

    cached = context.get_cache("cost_arrays")
    if cached is not None:
        return cached

    gross = np.nan_to_num(_resolve_gross(context))
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

    context.set_cache(
        "cost_arrays",
        (brokerage, slippage, swaps, gross)
    )

    return brokerage, slippage, swaps, gross


def cost_summary(context):

    brokerage, slippage, swaps, gross = _get_cost_arrays(context)

    if gross.size == 0:
        return None

    total_brokerage = np.sum(brokerage)
    total_slippage = np.sum(slippage)
    total_swaps = np.sum(swaps)

    total_cost = total_brokerage + total_slippage + total_swaps
    cost_per_trade = total_cost / gross.size

    gross_total = np.sum(gross)
    cost_ratio = (
        total_cost / gross_total
        if gross_total != 0 else None
    )

    return {
        "total_brokerage": float(total_brokerage),
        "total_slippage": float(total_slippage),
        "total_swaps": float(total_swaps),
        "total_cost": float(total_cost),
        "cost_per_trade": float(cost_per_trade),
        "cost_ratio": float(cost_ratio) if cost_ratio else None
    }


registry.register(
    "cost_summary",
    cost_summary,
    category="journal"
)