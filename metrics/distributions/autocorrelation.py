import numpy as np
from core.registry import registry


def autocorrelation(context):
    """
    Institutional Serial Dependence Detector

    - Detects return autocorrelation
    - Detects volatility clustering via squared returns
    - Adaptive lag selection
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None:
        return None

    n = returns.size

    if n < 30:
        return None

    max_lag = max(1, min(20, n // 10))

    mean = np.mean(returns)
    var = np.var(returns, ddof=1)

    if var == 0:
        return None

    squared = returns ** 2
    sq_mean = np.mean(squared)
    sq_var = np.var(squared, ddof=1)

    acf = []
    acf_sq = []

    for lag in range(1, max_lag + 1):

        cov = np.sum(
            (returns[:-lag] - mean) *
            (returns[lag:] - mean)
        ) / (n - lag)

        acf.append(cov / var)

        cov_sq = np.sum(
            (squared[:-lag] - sq_mean) *
            (squared[lag:] - sq_mean)
        ) / (n - lag)

        acf_sq.append(
            cov_sq / sq_var if sq_var > 0 else 0
        )

    threshold = 2 / np.sqrt(n)

    significant_lags = [
        lag + 1
        for lag, val in enumerate(acf)
        if abs(val) > threshold
    ]

    return {
        "acf_returns": acf,
        "acf_squared_returns": acf_sq,
        "significance_threshold": float(threshold),
        "significant_lags": significant_lags
    }


registry.register(
    "autocorrelation",
    autocorrelation,
    category="distributions",
    dependencies=["student_t_fit"]
)