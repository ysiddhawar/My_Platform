import numpy as np
from core.registry import registry


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
# AVERAGE WIN
# ==========================================================
def average_win(context):

    returns = _get_clean_returns(context)

    wins = returns[returns > 0]
    if wins.size == 0:
        return None

    return float(np.mean(wins))


registry.register(
    "average_win",
    average_win,
    category="journal"
)


# ==========================================================
# AVERAGE LOSS
# ==========================================================
def average_loss(context):

    returns = _get_clean_returns(context)

    losses = returns[returns < 0]
    if losses.size == 0:
        return None

    return float(np.mean(losses))


registry.register(
    "average_loss",
    average_loss,
    category="journal"
)


# ==========================================================
# PAYOFF RATIO
# ==========================================================
def payoff_ratio(context):

    avg_win = context.get_result("average_win")
    avg_loss = context.get_result("average_loss")

    if avg_win is None or avg_loss is None:
        return None

    avg_loss = abs(avg_loss)

    if avg_loss == 0:
        return None

    return float(avg_win / avg_loss)


registry.register(
    "payoff_ratio",
    payoff_ratio,
    category="journal",
    dependencies=["average_win", "average_loss"]
)