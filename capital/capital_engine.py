import numpy as np
from core.registry import registry


def capital_engine(context):

    aligned = context.get_cache("aligned_strategy_returns")
    cov = context.get_result("covariance_matrix")
    rb = context.get_result("risk_budgeting")
    kelly = context.get_result("kelly")

    total_capital = context.data.get("capital", 0)
    target_vol = context.data.get("target_volatility", 0.15)
    dd_thresh = context.data.get("max_drawdown_threshold", 0.25)
    max_leverage = context.data.get("max_leverage", 5.0)

    if (
        aligned is None or
        cov is None or
        rb is None or
        kelly is None or
        total_capital <= 0
    ):
        return None

    names, R = aligned
    cov = np.asarray(cov, dtype=np.float64)

    # -----------------------------------------
    # Safe Mapping
    # -----------------------------------------
    weights = np.array([
        float(rb.get(name, 0))
        for name in names
    ])

    if np.sum(weights) == 0:
        return None

    weights /= np.sum(weights)

    # -----------------------------------------
    # Portfolio Vol Targeting
    # -----------------------------------------
    port_vol = np.sqrt(weights @ cov @ weights)

    if port_vol > 0:
        weights *= (target_vol / port_vol)

    # -----------------------------------------
    # Kelly Edge Scaling
    # -----------------------------------------
    for i, name in enumerate(names):
        edge = float(kelly.get(name, 0))
        weights[i] *= max(edge, 0)

    # -----------------------------------------
    # Leverage Constraint
    # -----------------------------------------
    weights = np.clip(weights, 0, max_leverage)

    if np.sum(weights) == 0:
        return None

    weights /= np.sum(weights)

    # -----------------------------------------
    # Drawdown Survival Layer
    # -----------------------------------------
    portfolio_returns = np.sum(R.T * weights, axis=1)

    equity = np.cumprod(1 + portfolio_returns)
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak

    max_dd = abs(np.min(dd))

    if max_dd > dd_thresh:
        weights *= 0.5

    weights /= np.sum(weights)

    capital_alloc = {
        name: float(w * total_capital)
        for name, w in zip(names, weights)
    }

    return capital_alloc


registry.register(
    "capital_engine",
    capital_engine,
    category="capital",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix",
        "risk_budgeting",
        "kelly"
    ]
)