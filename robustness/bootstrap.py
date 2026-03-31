import numpy as np
from scipy import stats
from core.registry import registry


def bootstrap(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 20:
        return None

    kurt = stats.kurtosis(returns, fisher=True)

    confidence = 0.99 if n > 1000 else 0.95
    alpha = 1 - confidence

    n_resamples = int(np.clip(n*5, 200, 5000))
    if kurt > 3:
        n_resamples *= 2

    rng = np.random.default_rng()

    metrics = []

    for _ in range(n_resamples):

        sample = rng.choice(returns, size=n, replace=True)

        mean = np.mean(sample)
        std  = np.std(sample, ddof=1)

        val = mean/std if std>0 else 0

        if np.isfinite(val):
            metrics.append(val)

    if len(metrics) < 10:
        return None

    metrics = np.asarray(metrics)

    lower  = np.percentile(metrics, alpha*100)
    median = np.median(metrics)
    upper  = np.percentile(metrics,(1-alpha)*100)

    return {
        "median": float(median),
        "lower": float(lower),
        "upper": float(upper),
        "instability": float(upper-lower),
        "fat_tail": bool(kurt>3)
    }


registry.register(
    "bootstrap",
    bootstrap,
    category="robustness",
    dependencies=["adjusted_pnl"]
)