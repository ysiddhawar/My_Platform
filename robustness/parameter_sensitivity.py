import numpy as np
from core.registry import registry


def parameter_sensitivity(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 50:
        return None

    param_range = np.linspace(
        5,
        int(np.sqrt(n)),
        10
    ).astype(int)

    sharpe_values = []

    for window in param_range:

        if window >= n:
            continue

        rolling = [
            np.mean(returns[i-window:i])
            for i in range(window, n)
        ]

        rolling = np.asarray(rolling)

        if rolling.size < 10:
            continue

        mu = np.mean(rolling)
        sigma = np.std(rolling, ddof=1)

        if sigma == 0:
            continue

        sharpe_values.append(mu/sigma)

    if len(sharpe_values) < 3:
        return None

    sharpe_values = np.asarray(sharpe_values)

    mean = np.mean(sharpe_values)
    std  = np.std(sharpe_values)

    return {
        "mean_sharpe": float(mean),
        "sharpe_std": float(std),
        "fragility_score": float(std/abs(mean)) if mean!=0 else None
    }


registry.register(
    "parameter_sensitivity",
    parameter_sensitivity,
    category="robustness",
    dependencies=["adjusted_pnl"]
)