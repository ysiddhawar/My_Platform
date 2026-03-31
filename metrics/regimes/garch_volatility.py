import numpy as np
from core.registry import registry


def garch_volatility(context):
    """
    Adaptive GARCH(1,1) Conditional Volatility

    Estimates time-varying volatility
    from net-adjusted return stream.
    """

    returns = context.get_cache("dist_clean_returns")
    if returns is None:
        returns = context.get_cache("net_returns")
    if returns is None:
        returns = np.asarray(
            context.data.get("returns", []),
            dtype=np.float64
        )
        returns = returns[~np.isnan(returns)]

    if returns is None or returns.size < 100:
        return None

    eps = returns - np.mean(returns)

    var_init = np.var(eps)

    alpha = min(0.1, 0.02 + 0.5 / np.sqrt(returns.size))
    beta = min(0.95, 0.85 + 0.5 / np.sqrt(returns.size))
    omega = var_init * (1 - alpha - beta)

    sigma2 = np.zeros(eps.size)
    sigma2[0] = var_init

    for t in range(1, eps.size):
        sigma2[t] = (
            omega +
            alpha * eps[t-1]**2 +
            beta * sigma2[t-1]
        )

    return {
        "conditional_vol": float(np.sqrt(sigma2[-1])),
        "persistence": float(alpha + beta)
    }


registry.register(
    "garch_volatility",
    garch_volatility,
    category="regimes",
    dependencies=["adjusted_pnl"]
)