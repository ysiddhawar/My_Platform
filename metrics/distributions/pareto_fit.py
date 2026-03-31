import numpy as np
from scipy import stats
from core.registry import registry


def pareto_fit(context):
    """
    Institutional Pareto Tail Fit

    - Uses cost-adjusted net return distribution
    - Models extreme negative loss tail
    - Returns alpha (tail index)
    - KS goodness-of-fit for model validity
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 100:
        return None

    losses = -returns[returns < 0]

    if losses.size < 50:
        return None

    tail_quantile = max(0.90, 1 - 10 / losses.size)
    threshold = np.quantile(losses, tail_quantile)

    tail = losses[losses >= threshold]

    if tail.size < 30:
        return None

    excess = tail - threshold

    try:
        params = stats.pareto.fit(excess, floc=0)
        alpha = params[0]

        ks_stat, _ = stats.kstest(excess, 'pareto', args=params)

        return {
            "pareto_alpha": float(alpha),
            "tail_threshold": float(threshold),
            "tail_fraction": float(tail.size / losses.size),
            "ks_statistic": float(ks_stat)
        }

    except Exception:
        return None


registry.register(
    "pareto_fit",
    pareto_fit,
    category="distributions",
    dependencies=["student_t_fit"]
)