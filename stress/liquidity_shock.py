import numpy as np
from core.registry import registry


def liquidity_shock(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    names, R = aligned
    R = np.asarray(R, dtype=np.float64)

    spreads = context.data.get("spread_matrix")
    if spreads is None:
        return None

    S = np.asarray(spreads, dtype=np.float64)

    if S.shape != R.shape:
        return None

    n, T = R.shape
    if T < 50:
        return None

    lookback_ratio = context.data.get("liq_lookback_ratio", 0.2)
    spread_percentile = context.data.get("spread_percentile", 95)
    slippage_multiplier = context.data.get("slippage_multiplier", 3.0)

    lookback = max(30, int(T * lookback_ratio))

    results = {}

    for i in range(n):

        r = R[i]
        s = S[i]

        recent_spreads = s[-lookback:]

        threshold = np.percentile(recent_spreads, spread_percentile)
        shock_mask = s > threshold

        stressed = r.copy()
        stressed[shock_mask] -= s[shock_mask] * slippage_multiplier

        impact = np.sum(stressed) - np.sum(r)

        results[names[i]] = {
            "spread_threshold": float(threshold),
            "liquidity_spike": bool(s[-1] > threshold),
            "stress_pnl_impact": float(impact)
        }

    context.set_cache("liquidity_shock", results)

    return results


registry.register(
    "liquidity_shock",
    liquidity_shock,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)