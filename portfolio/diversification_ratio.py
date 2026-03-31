import numpy as np
from core.registry import registry


def diversification_ratio(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    _, N = R.shape

    cov = context.get_result("covariance_matrix")
    if cov is None:
        return None

    cov = np.asarray(cov, dtype=np.float64)

    weights = context.get_result("risk_parity")

    if weights is None:
        w = np.ones(N) / N
    else:
        w = np.array([weights[n] for n in names], dtype=np.float64)

    if np.sum(w) <= 1e-12:
        return None

    w /= np.sum(w)

    vols = np.sqrt(np.diag(cov))
    if np.any(vols <= 1e-12):
        return None

    weighted_vol = w.T @ vols
    port_vol = np.sqrt(w.T @ cov @ w)

    if port_vol <= 1e-12:
        return None

    return float(weighted_vol / port_vol)


registry.register(
    "diversification_ratio",
    diversification_ratio,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix",
        "risk_parity"
    ]
)