import numpy as np
from scipy import stats
from core.registry import registry


def covariance_matrix(context):

    R = context.get_cache("strategy_returns")

    if R is None:
        return None

    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2 or R.shape[1] < 2:
        return None

    T, N = R.shape

    if T < 30:
        return None

    kurt = np.mean([
        stats.kurtosis(R[:, i], fisher=True)
        for i in range(N)
    ])

    if kurt > 1:
        centered = R - np.median(R, axis=0)
        cov = np.dot(centered.T, centered) / (T - 1)
    else:
        cov = np.cov(R, rowvar=False)

    context.set_cache("covariance_matrix", cov)

    return cov.tolist()


registry.register(
    "covariance_matrix",
    covariance_matrix,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)