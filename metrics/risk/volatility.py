import numpy as np
from core.registry import registry


def volatility(context):
    """
    Institutional Adaptive Volatility

    - Uses net returns
    - Sampling frequency inferred
    - Annualized
    """

    returns = context.get_cache("net_returns")

    if returns is None or returns.size < 10:
        return None

    n = returns.size

    if n > 5000:
        periods = 252 * 6.5 * 60
    elif n > 1000:
        periods = 252 * 6.5
    else:
        periods = 252

    std = np.std(returns, ddof=1)

    return float(std * np.sqrt(periods))


registry.register(
    "volatility",
    volatility,
    category="risk",
    dependencies=["adjusted_pnl"]
)