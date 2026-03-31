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

    returns = returns[~np.isnan(returns)]

    context.set_cache("clean_returns", returns)

    return returns


# ==========================================================
# WIN RATE
# ==========================================================
def win_rate(context):

    returns = _get_clean_returns(context)

    n = returns.size
    if n == 0:
        return None

    wins = np.sum(returns > 0)

    return float(wins / n)


registry.register(
    "win_rate",
    win_rate,
    category="journal",
    dependencies=["trade_count"]
)


# ==========================================================
# LOSS RATE
# ==========================================================
def loss_rate(context):

    returns = _get_clean_returns(context)

    n = returns.size
    if n == 0:
        return None

    losses = np.sum(returns < 0)

    return float(losses / n)


registry.register(
    "loss_rate",
    loss_rate,
    category="journal",
    dependencies=["trade_count"]
)