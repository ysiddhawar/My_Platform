import numpy as np
from core.registry import registry


def risk_parity(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    _, N = R.shape

    cov = context.get_result("covariance_matrix")
    if cov is None:
        return None

    cov = np.asarray(cov, dtype=np.float64)

    w = np.ones(N) / N

    max_iter = int(N * 400)
    tol = 1e-5

    for _ in range(max_iter):

        port_vol = np.sqrt(w.T @ cov @ w)
        if port_vol <= 1e-12:
            return None

        mrc = (cov @ w) / port_vol
        rc = w * mrc

        total_rc = np.sum(rc)
        if total_rc <= 1e-12:
            return None

        prc = rc / total_rc
        target = np.ones(N) / N
        diff = prc - target

        if np.max(np.abs(diff)) < tol:
            break

        w *= (1 - diff)
        w = np.maximum(w, 1e-10)
        w /= np.sum(w)

    return dict(zip(names, w.tolist()))


registry.register(
    "risk_parity",
    risk_parity,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix"
    ]
)