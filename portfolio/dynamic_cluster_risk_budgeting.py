import numpy as np
from core.registry import registry


def dynamic_cluster_risk_budgeting(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2 or R.shape[1] < 50:
        return None

    # -----------------------------------------
    # Base Allocation (HRP)
    # -----------------------------------------
    base = context.get_result("hierarchical_risk_parity")
    if base is None:
        return None

    w = np.array([base[k] for k in keys])
    if np.sum(w) == 0:
        return None

    w = w / np.sum(w)

    # -----------------------------------------
    # Rolling Volatility (Regime Proxy)
    # -----------------------------------------
    vol = np.std(R[:, -50:], axis=1, ddof=1)

    if np.any(vol == 0):
        return None

    inv_vol = 1 / vol
    regime_adj = inv_vol / np.sum(inv_vol)

    # -----------------------------------------
    # Tail Stress Penalty
    # -----------------------------------------
    tail = np.percentile(R[:, -50:], 5, axis=1)
    stress = np.abs(tail)

    if np.sum(stress) == 0:
        return None

    stress_adj = stress / np.sum(stress)

    # -----------------------------------------
    # Final Budget Adjustment
    # -----------------------------------------
    final = w * regime_adj * (1 - stress_adj)

    if np.sum(final) == 0:
        return None

    final = final / np.sum(final)

    return dict(zip(keys, final.tolist()))


registry.register(
    "dynamic_cluster_risk_budgeting",
    dynamic_cluster_risk_budgeting,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "hierarchical_risk_parity"
    ]
)