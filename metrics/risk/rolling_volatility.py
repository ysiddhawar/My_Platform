import numpy as np
from core.registry import registry


def rolling_volatility(context):
    """
    Rolling annualized volatility series from net returns.
    """

    returns = context.get_cache("net_returns")
    if returns is None:
        return None

    r = np.asarray(returns, dtype=np.float64)
    if r.size < 20:
        return None

    n = r.size
    if n > 5000:
        periods = 252 * 6.5 * 60
    elif n > 1000:
        periods = 252 * 6.5
    else:
        periods = 252

    window = int(context.data.get("rolling_vol_window", 20))
    if window < 2:
        window = 2
    if r.size < window:
        return None

    vals = []
    for i in range(window, r.size + 1):
        vals.append(np.std(r[i - window:i], ddof=1) * np.sqrt(periods))

    out = np.asarray(vals, dtype=np.float64)
    context.set_cache("rolling_volatility_series", out)
    return out


registry.register(
    "rolling_volatility",
    rolling_volatility,
    category="risk",
    dependencies=["adjusted_pnl"],
)
