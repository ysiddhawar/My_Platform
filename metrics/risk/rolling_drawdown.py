import numpy as np
from core.registry import registry


def rolling_drawdown(context):
    """
    Adaptive Rolling Drawdown

    Computes rolling worst drawdown using:
    - cost-adjusted net returns
    - adaptive window sizing
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    n = returns.size

    if n < 30:
        return None

    window = max(20, int(n * 0.1))

    rolling_dd = np.empty(n - window + 1)

    for i in range(window, n + 1):

        segment = returns[i - window:i]

        equity = np.cumprod(1 + segment)
        peaks = np.maximum.accumulate(equity)
        dd = (equity - peaks) / peaks

        rolling_dd[i - window] = np.min(dd)

    return rolling_dd


registry.register(
    "rolling_drawdown",
    rolling_drawdown,
    category="risk",
    dependencies=["adjusted_pnl"]
)