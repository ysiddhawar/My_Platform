import numpy as np
from core.registry import registry


def adaptive_rolling_volatility(context):
    """
    Adaptive Rolling Volatility

    - Uses cost-adjusted net returns
    - Window auto-scales with data length
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    n = returns.size

    if n < 30:
        return None

    window = max(20, int(n * 0.05))

    rvol = np.empty(n - window + 1)

    for i in range(window, n + 1):

        chunk = returns[i - window:i]

        rvol[i - window] = np.std(chunk, ddof=1)

    return rvol


registry.register(
    "adaptive_rolling_volatility",
    adaptive_rolling_volatility,
    category="risk",
    dependencies=["adjusted_pnl"]
)