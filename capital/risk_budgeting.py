import numpy as np
from core.registry import registry


def risk_budgeting(context):

    cov = context.get_result("covariance_matrix")
    aligned = context.get_cache("aligned_strategy_returns")

    if cov is None or aligned is None:
        return None

    keys, _ = aligned
    cov = np.asarray(cov, dtype=np.float64)

    n = len(keys)

    target_budget = context.data.get("risk_budget")

    if target_budget is None:
        target_budget = np.ones(n) / n
    else:
        target_budget = np.asarray(target_budget, dtype=np.float64)
        target_budget = target_budget / np.sum(target_budget)

    w = np.ones(n) / n
    tol = 1e-6
    max_iter = int(500 + 50 * n)

    for _ in range(max_iter):

        port_vol = np.sqrt(w.T @ cov @ w)
        if port_vol == 0:
            return None

        mrc = (cov @ w) / port_vol
        rc = w * mrc
        frac = rc / np.sum(rc)

        diff = frac - target_budget

        if np.max(np.abs(diff)) < tol:
            break

        w *= (1 - diff)
        w = np.maximum(w, 1e-8)
        w /= np.sum(w)

    return dict(zip(keys, w.tolist()))


registry.register(
    "risk_budgeting",
    risk_budgeting,
    category="capital",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix"
    ]
)