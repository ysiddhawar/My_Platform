import numpy as np
from core.registry import registry


def target_volatility(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    _, N = R.shape

    cov = context.get_result("covariance_matrix")
    if cov is None:
        return None

    cov = np.asarray(cov, dtype=np.float64)

    base_w = context.get_result("risk_parity")

    if base_w is None:
        w = np.ones(N) / N
    else:
        w = np.array([base_w[n] for n in names], dtype=np.float64)

    current_vol = np.sqrt(w.T @ cov @ w)
    if current_vol <= 1e-12:
        return None

    target_vol = context.data.get("target_volatility", 0.15)
    scale = target_vol / current_vol

    scaled_w = w * scale

    return dict(zip(names, scaled_w.tolist()))


registry.register(
    "target_volatility",
    target_volatility,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix",
        "risk_parity"
    ]
)