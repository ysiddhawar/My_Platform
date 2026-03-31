import numpy as np
from core.registry import registry


def drawdown_aware_capital_allocator(context):
    """
    Drawdown-Aware Capital Allocator (Institutional)

    Purpose
    -------
    Dynamically penalizes strategies exhibiting persistent
    equity curve deterioration (capital destruction path),
    even when volatility and correlation appear stable.

    This allocator:
    - Detects rolling drawdown persistence
    - Applies adaptive capital penalty
    - Reallocates towards equity-stable strategies
    - Works as final allocator override layer
    - Institutional capital-preservation safeguard

    Requires:
    ---------
    portfolio_preprocessor
    hierarchical_risk_parity
    """

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2:
        return None

    n_assets, n_obs = R.shape

    if n_assets < 2 or n_obs < 50:
        return None

    # -----------------------------------------
    # Base weights (HRP preferred)
    # -----------------------------------------
    base = context.get_result("hierarchical_risk_parity")

    if base is None:
        base = np.ones(n_assets) / n_assets
    else:
        base = np.array(list(base.values()), dtype=np.float64)

    if np.sum(base) == 0:
        return None

    base = base / np.sum(base)

    # -----------------------------------------
    # Rolling drawdown persistence detection
    # -----------------------------------------
    window = max(20, int(0.1 * n_obs))

    dd_persistence = np.zeros(n_assets)

    for i in range(n_assets):

        r = R[i]

        equity = np.cumprod(1 + r)
        peaks = np.maximum.accumulate(equity)
        dd = (equity - peaks) / peaks

        rolling_dd = []

        for t in range(window, len(dd)):
            segment = dd[t - window:t]
            rolling_dd.append(np.mean(segment))

        rolling_dd = np.array(rolling_dd)

        if rolling_dd.size == 0:
            continue

        # persistence = % time spent in sustained DD
        dd_persistence[i] = np.mean(rolling_dd < -0.02)

    # -----------------------------------------
    # Penalization Curve (adaptive)
    # -----------------------------------------
    penalty = 1 - dd_persistence

    penalty = np.clip(penalty, 0.1, 1.0)

    adjusted = base * penalty

    if np.sum(adjusted) == 0:
        return None

    adjusted /= np.sum(adjusted)

    return dict(zip(keys, adjusted.tolist()))


registry.register(
    "drawdown_aware_capital_allocator",
    drawdown_aware_capital_allocator,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "hierarchical_risk_parity"
    ]
)