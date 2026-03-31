import numpy as np
from core.registry import registry


def walk_forward(context):
    """
    Walk-Forward Stability Engine
    Uses net_returns (cost-adjusted)
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 50:
        return None

    window = max(30, int(n * 0.3))

    performances = []

    for i in range(window, n):

        train = returns[i-window:i]
        test  = returns[i]

        if train.size < 20:
            continue

        mu = np.mean(train)

        signal = 1 if mu > 0 else -1
        out = signal * test

        if np.isfinite(out):
            performances.append(out)

    if len(performances) < 10:
        return None

    performances = np.asarray(performances)

    return {
        "mean_oos": float(np.mean(performances)),
        "stability_ratio": float(np.mean(performances > 0)),
        "cumulative": float(np.prod(1+performances)-1)
    }


registry.register(
    "walk_forward",
    walk_forward,
    category="robustness",
    dependencies=["adjusted_pnl"]
)