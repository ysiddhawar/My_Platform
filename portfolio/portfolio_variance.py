import numpy as np
from core.registry import registry


def portfolio_variance(context):

    cov = context.get_result("covariance_matrix")

    weights = context.data.get("portfolio_weights")

    if cov is None:
        return None

    cov = np.asarray(cov, dtype=np.float64)

    n = cov.shape[0]

    if weights is None:
        w = np.ones(n) / n
    else:
        w = np.asarray(weights, dtype=np.float64)
        if np.sum(w) == 0:
            return None
        w = w / np.sum(w)

    var = w.T @ cov @ w

    return float(var)


registry.register(
    "portfolio_variance",
    portfolio_variance,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "covariance_matrix"
    ]
)