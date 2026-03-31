import numpy as np
from core.registry import registry


def regime_drawdown(context):
    """
    Computes Max Drawdown per Volatility Regime
    using net-adjusted return stream.
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

    regime_returns = {
        "LOW": [],
        "MEDIUM": [],
        "HIGH": []
    }

    for i in range(window, n):

        vol = np.std(returns[i-window:i], ddof=1)
        r = returns[i]

        if vol <= low:
            regime_returns["LOW"].append(r)
        elif vol <= high:
            regime_returns["MEDIUM"].append(r)
        else:
            regime_returns["HIGH"].append(r)

    results = {}

    for k, data in regime_returns.items():

        data = np.array(data)
        if data.size < 20:
            results[k] = None
            continue

        equity = np.cumprod(1 + data)
        peaks = np.maximum.accumulate(equity)
        dd = (equity - peaks) / peaks

        results[k] = float(np.min(dd))

    return results


registry.register(
    "regime_drawdown",
    regime_drawdown,
    category="regimes",
    dependencies=["volatility_regime"]
)