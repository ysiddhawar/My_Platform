import numpy as np
from core.registry import registry


def risk_contribution(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    T, N = R.shape
    if T < 30 or N < 2:
        return None

    cov = context.get_result("covariance_matrix")
    if cov is None:
        return None

    cov = np.asarray(cov, dtype=np.float64)

    w = np.ones(N) / N

    port_vol = np.sqrt(w.T @ cov @ w)
    if port_vol <= 1e-12:
        return None

    mrc = (cov @ w) / port_vol
    rc = w * mrc

    total_rc = np.sum(rc)
    if total_rc <= 1e-12:
        return None

    prc = rc / total_rc

    return {
        "mrc": dict(zip(names, mrc.tolist())),
        "rc": dict(zip(names, rc.tolist())),
        "prc": dict(zip(names, prc.tolist()))
    }


registry.register(
    "risk_contribution",
    risk_contribution,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix"
    ]
)