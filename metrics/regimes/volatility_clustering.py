import numpy as np
from core.registry import registry


def volatility_clustering(context):
    """
    Volatility Clustering Score

    Measures persistence of volatility using
    autocorrelation of squared net returns.
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 50:
        return None

    squared = returns ** 2
    mean_sq = np.mean(squared)

    max_lag = max(5, int(returns.size ** 0.3))
    autocorrs = []

    for lag in range(1, max_lag + 1):
        x = squared[:-lag]
        y = squared[lag:]

        num = np.sum((x - mean_sq) * (y - mean_sq))
        den = np.sum((squared - mean_sq) ** 2)

        autocorrs.append(num / den if den > 0 else 0.0)

    return float(np.mean(np.abs(autocorrs)))


registry.register(
    "volatility_clustering",
    volatility_clustering,
    category="regimes",
    dependencies=["adjusted_pnl"]
)