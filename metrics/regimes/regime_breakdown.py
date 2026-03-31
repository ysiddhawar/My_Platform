import numpy as np
from core.registry import registry


def regime_breakdown(context):
    """
    Evaluates performance stability
    across volatility regimes.
    """

    returns = context.get_cache("dist_clean_returns")
    vr = context.get_result("volatility_regime")

    if returns is None or vr is None:
        return None

    window = vr["window"]
    low = vr["low_threshold"]
    high = vr["high_threshold"]

    n = returns.size
    if n <= window:
        return None

    buckets = {
        "LOW": [],
        "MEDIUM": [],
        "HIGH": []
    }

    for i in range(window, n):

        vol = np.std(returns[i-window:i], ddof=1)
        r = returns[i]

        if vol <= low:
            buckets["LOW"].append(r)
        elif vol <= high:
            buckets["MEDIUM"].append(r)
        else:
            buckets["HIGH"].append(r)

    results = {}

    for k, data in buckets.items():

        data = np.array(data)
        if data.size < 20:
            results[k] = None
            continue

        mean = np.mean(data)
        std = np.std(data, ddof=1)

        equity = np.cumprod(1 + data)
        peaks = np.maximum.accumulate(equity)
        dd = (equity - peaks) / peaks

        sharpe = mean / std if std > 0 else None

        results[k] = {
            "observations": int(data.size),
            "mean_return": float(mean),
            "volatility": float(std),
            "sharpe": float(sharpe) if sharpe else None,
            "max_drawdown": float(np.min(dd))
        }

    return results


registry.register(
    "regime_breakdown",
    regime_breakdown,
    category="regimes",
    dependencies=[
        "adjusted_pnl",
        "volatility_regime"
    ]
)