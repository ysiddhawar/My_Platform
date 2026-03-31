import numpy as np
from core.registry import registry


def power_law_fit(context):
    """
    Institutional Power-Law Tail Fit (Hill Estimator)

    - Uses cost-adjusted net returns
    - Detects heavy-tail decay strength
    - Lower alpha → fatter crash tail
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 100:
        return None

    losses = -returns[returns < 0]

    if losses.size < 30:
        return None

    losses = np.sort(losses)

    k = max(20, int(losses.size * 0.10))
    tail = losses[-k:]

    x_min = tail[0]

    if x_min <= 0:
        return None

    hill_estimator = k / np.sum(np.log(tail / x_min))

    return float(hill_estimator)


registry.register(
    "power_law_fit",
    power_law_fit,
    category="distributions",
    dependencies=["student_t_fit"]
)