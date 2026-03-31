import numpy as np
from core.registry import registry


# ---------------------------------------------------------
# INTERNAL: Fetch Net Research Returns
# ---------------------------------------------------------
def _get_research_returns(context):

    # Prefer net-of-cost returns written by adjusted_pnl
    cached = context.get_cache("net_returns")
    if cached is not None:
        return cached

    # Fallback (if adjusted_pnl skipped)
    returns = np.asarray(
        context.data.get("returns", []),
        dtype=np.float64
    )

    returns = returns[~np.isnan(returns)]

    context.set_cache("clean_returns", returns)

    return returns


# =========================================================
# PROFIT FACTOR (NET-OF-COST)
# =========================================================
def profit_factor(context):

    returns = _get_research_returns(context)

    if returns.size == 0:
        return None

    gross_profit = np.sum(returns[returns > 0])
    gross_loss = np.abs(np.sum(returns[returns < 0]))

    if gross_loss == 0:
        return None

    return float(gross_profit / gross_loss)


registry.register(
    "profit_factor",
    profit_factor,
    category="journal",
    dependencies=["adjusted_pnl"]
)


# =========================================================
# EXPECTANCY (NET-OF-COST DAG SAFE)
# =========================================================
def expectancy(context):

    returns = _get_research_returns(context)

    if returns.size == 0:
        return None

    wins = returns[returns > 0]
    losses = returns[returns < 0]

    n = returns.size
    wr = wins.size / n
    lr = losses.size / n

    aw = np.mean(wins) if wins.size > 0 else 0.0
    al = np.mean(losses) if losses.size > 0 else 0.0

    return float((wr * aw) + (lr * al))


registry.register(
    "expectancy",
    expectancy,
    category="journal",
    dependencies=["adjusted_pnl"]
)