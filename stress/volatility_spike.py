import numpy as np
from core.registry import registry


def volatility_spike(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    names, R = aligned
    R = np.asarray(R, dtype=np.float64)

    n, T = R.shape
    if T < 50:
        return None

    lookback_ratio = context.data.get("vol_lookback_ratio", 0.2)
    ewma_lambda = context.data.get("ewma_lambda", 0.94)
    spike_percentile = context.data.get("vol_spike_percentile", 99)

    lookback = max(30, int(T * lookback_ratio))
    recent = R[:, -lookback:]

    results = {}

    for i in range(n):

        r = recent[i]

        ewma_var = np.zeros(len(r))
        ewma_var[0] = np.var(r)

        for t in range(1, len(r)):
            ewma_var[t] = (
                ewma_lambda * ewma_var[t-1]
                + (1 - ewma_lambda) * r[t-1]**2
            )

        ewma_vol = np.sqrt(ewma_var)

        threshold = np.percentile(ewma_vol, spike_percentile)
        spike = ewma_vol[-1] > threshold

        results[names[i]] = {
            "current_vol": float(ewma_vol[-1]),
            "vol_threshold": float(threshold),
            "vol_spike": bool(spike)
        }

    context.set_cache("volatility_spike", results)

    return results


registry.register(
    "volatility_spike",
    volatility_spike,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)