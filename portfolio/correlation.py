import numpy as np
from scipy import stats
from core.registry import registry


def correlation(context):

    R = context.get_cache("strategy_returns")

    if R is None:
        return None

    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2 or R.shape[1] < 2:
        return None

    T, N = R.shape

    if T < 30:
        return None

    corr_matrix = np.zeros((N, N), dtype=np.float64)

    for i in range(N):
        for j in range(i, N):

            a = R[:, i]
            b = R[:, j]

            kurt_a = stats.kurtosis(a, fisher=True)
            kurt_b = stats.kurtosis(b, fisher=True)

            if kurt_a > 1 or kurt_b > 1:
                corr, _ = stats.spearmanr(a, b)
            else:
                corr = np.corrcoef(a, b)[0, 1]

            if np.isnan(corr):
                corr = 0.0

            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr

    context.set_cache("correlation_matrix", corr_matrix)

    return corr_matrix.tolist()


registry.register(
    "correlation",
    correlation,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)