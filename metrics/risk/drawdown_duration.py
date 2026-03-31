import numpy as np
from core.registry import registry


def drawdown_duration(context):
    """
    Maximum Drawdown Duration

    Longest consecutive time capital remained below peak.
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    n = returns.size

    if n < 20:
        return None

    equity = np.cumprod(1 + returns)
    peaks = np.maximum.accumulate(equity)

    in_dd = equity < peaks

    max_duration = 0
    current = 0

    for flag in in_dd:
        if flag:
            current += 1
            max_duration = max(max_duration, current)
        else:
            current = 0

    return int(max_duration)


registry.register(
    "drawdown_duration",
    drawdown_duration,
    category="risk",
    dependencies=["adjusted_pnl"]
)