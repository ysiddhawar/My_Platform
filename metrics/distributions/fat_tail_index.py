import numpy as np
from scipy import stats
from core.registry import registry


def fat_tail_index(context):
    """
    Institutional Fat Tail Severity Estimator

    - Uses cost-adjusted net returns
    - Cached distribution stream
    - Compares empirical tail probability vs Gaussian expectation
    - >1 = fatter tails than normal
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 50:
        return None

    mean = np.mean(returns)
    std = np.std(returns, ddof=1)

    if std <= 0:
        return 0.0

    threshold = mean - 3 * std

    empirical_tail_prob = np.mean(returns < threshold)

    normal_tail_prob = stats.norm.cdf(threshold, loc=mean, scale=std)

    if normal_tail_prob <= 0:
        return None

    fti = empirical_tail_prob / normal_tail_prob

    return float(fti)


registry.register(
    "fat_tail_index",
    fat_tail_index,
    category="distributions",
    dependencies=["normality_test"]
)