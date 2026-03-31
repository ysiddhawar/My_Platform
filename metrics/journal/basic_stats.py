import numpy as np
from core.registry import registry


# ----------------------------------------------------------
# INTERNAL SAFE EXTRACTION
# ----------------------------------------------------------
def _get_clean_returns(context):

    cached = context.get_cache("clean_returns")

    if cached is not None:
        return cached

    returns = np.asarray(
        context.data.get("returns", []),
        dtype=np.float64
    )
    if returns.size == 0:
        returns = np.asarray(
            context.data.get("gross_pnl", []),
            dtype=np.float64
        )
    if returns.size == 0:
        returns = np.asarray(
            context.data.get("net_pnl", []),
            dtype=np.float64
        )

    returns = returns[~np.isnan(returns)]

    context.set_cache("clean_returns", returns)

    return returns


# ==========================================================
# TRADE COUNT
# ==========================================================
def trade_count(context):

    returns = _get_clean_returns(context)

    if returns.size == 0:
        return 0

    return int(returns.size)


registry.register(
    "trade_count",
    trade_count,
    category="journal"
)


# ==========================================================
# WIN COUNT
# ==========================================================
def win_count(context):

    returns = _get_clean_returns(context)

    if returns.size == 0:
        return 0

    return int(np.sum(returns > 0))


registry.register(
    "win_count",
    win_count,
    category="journal",
    dependencies=["trade_count"]
)


# ==========================================================
# LOSS COUNT
# ==========================================================
def loss_count(context):

    returns = _get_clean_returns(context)

    if returns.size == 0:
        return 0

    return int(np.sum(returns < 0))


registry.register(
    "loss_count",
    loss_count,
    category="journal",
    dependencies=["trade_count"]
)