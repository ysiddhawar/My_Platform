import numpy as np
from core.registry import registry


def portfolio_position_sizer(context):
    """
    Institutional Portfolio Position Sizer

    Uses:
    - Portfolio covariance structure
    - Risk budgeting allocation
    - Strategy Kelly fractions
    - Target portfolio volatility

    Produces:
    - Per-strategy capital allocation
    """

    names_matrix = context.get_cache("aligned_strategy_returns")
    cov = context.get_result("covariance_matrix")
    kelly = context.get_result("kelly")

    total_capital = context.data.get("capital", 0)
    target_vol = context.data.get("target_vol", 0.15)
    max_leverage = context.data.get("max_leverage", 3.0)

    if (
        names_matrix is None or
        cov is None or
        kelly is None or
        total_capital <= 0
    ):
        return None

    names, R = names_matrix
    cov = np.asarray(cov, dtype=np.float64)

    n = len(names)
    weights = np.ones(n) / n

    # -----------------------------
    # Risk Parity Allocation
    # -----------------------------
    for _ in range(500):

        port_var = weights @ cov @ weights
        if port_var <= 0:
            return None

        port_vol = np.sqrt(port_var)

        marginal = (cov @ weights) / port_vol
        rc = weights * marginal
        rc_frac = rc / np.sum(rc)

        target = np.ones(n) / n
        diff = rc_frac - target

        if np.max(np.abs(diff)) < 1e-6:
            break

        weights *= (1 - diff)
        weights = np.maximum(weights, 0)
        weights /= np.sum(weights)

    # -----------------------------
    # Volatility Targeting
    # -----------------------------
    port_vol = np.sqrt(weights @ cov @ weights)

    if port_vol > 0:
        weights *= (target_vol / port_vol)

    # -----------------------------
    # Kelly Edge Scaling
    # -----------------------------
    for i, name in enumerate(names):
        edge = float(kelly.get(name, 0))
        weights[i] *= max(edge, 0)

    # -----------------------------
    # Leverage Constraints
    # -----------------------------
    weights = np.clip(weights, 0, max_leverage)

    if np.sum(weights) == 0:
        return None

    weights /= np.sum(weights)

    capital_alloc = {
        name: float(w * total_capital)
        for name, w in zip(names, weights)
    }

    return capital_alloc


registry.register(
    "portfolio_position_sizer",
    portfolio_position_sizer,
    category="capital",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix",
        "risk_budgeting",
        "kelly"
    ]
)