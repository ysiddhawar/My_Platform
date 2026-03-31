import numpy as np
from core.registry import registry


def volatility_regime(context):
    """
    Institutional Volatility Regime Detector

    - Uses net return distribution
    - Adaptive rolling window
    - Percentile-based volatility states
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None:
        return None

    n = returns.size
    if n < 50:
        return None

    window = max(20, int(n * 0.1))

    rolling_vol = np.array([
        np.std(returns[i-window:i], ddof=1)
        for i in range(window, n)
    ])

    low_thresh = np.percentile(rolling_vol, 33)
    high_thresh = np.percentile(rolling_vol, 66)

    regimes = np.where(
        rolling_vol <= low_thresh, "LOW",
        np.where(rolling_vol <= high_thresh, "MEDIUM", "HIGH")
    )

    return {
        "window": int(window),
        "low_threshold": float(low_thresh),
        "high_threshold": float(high_thresh),
        "latest_regime": regimes[-1],
        "regime_series": regimes.tolist()
    }


registry.register(
    "volatility_regime",
    volatility_regime,
    category="regimes",
    dependencies=["student_t_fit"]
)