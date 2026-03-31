import numpy as np
from core.registry import registry


def regime_sharpe(context):
    """
    Regime-Conditioned Sharpe

    - Computes Sharpe per volatility regime
    - Uses net return stream
    """

    returns = context.get_cache("dist_clean_returns")
    vr = context.get_result("volatility_regime")

    if returns is None or vr is None:
        return None

    window = vr["window"]
    low_thresh = vr["low_threshold"]
    high_thresh = vr["high_threshold"]

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

        if vol <= low_thresh:
            regime_returns["LOW"].append(r)
        elif vol <= high_thresh:
            regime_returns["MEDIUM"].append(r)
        else:
            regime_returns["HIGH"].append(r)

    sharpe = {}

    for k, data in regime_returns.items():

        data = np.array(data)
        if data.size < 20:
            sharpe[k] = None
            continue

        std = np.std(data, ddof=1)
        sharpe[k] = None if std == 0 else float(np.mean(data) / std)

    return sharpe


registry.register(
    "regime_sharpe",
    regime_sharpe,
    category="regimes",
    dependencies=["volatility_regime"]
)