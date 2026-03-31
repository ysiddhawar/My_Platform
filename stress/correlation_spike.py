import numpy as np
from core.registry import registry


def correlation_spike(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2 or R.shape[1] < 50:
        return None

    n_assets, T = R.shape
    lookback = max(30, int(T * 0.2))

    recent = R[:, -lookback:]

    corr_now = np.corrcoef(recent)
    upper_now = corr_now[np.triu_indices(n_assets, k=1)]
    current_avg = np.mean(np.abs(upper_now))

    historical = []

    for t in range(lookback, T):
        window = R[:, t - lookback:t]
        c = np.corrcoef(window)
        u = c[np.triu_indices(n_assets, k=1)]
        if np.all(np.isfinite(u)):
            historical.append(np.mean(np.abs(u)))

    if len(historical) < 5:
        return None

    hist = np.array(historical)

    mu = np.mean(hist)
    sigma = np.std(hist)

    zscore = (current_avg - mu) / sigma if sigma > 0 else 0

    spike = zscore > 2.0

    return {
        "avg_corr_now": float(current_avg),
        "historical_mean": float(mu),
        "historical_std": float(sigma),
        "corr_zscore": float(zscore),
        "correlation_spike": bool(spike)
    }


registry.register(
    "correlation_spike",
    correlation_spike,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)