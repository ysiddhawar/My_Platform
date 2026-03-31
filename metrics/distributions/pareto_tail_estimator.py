import numpy as np
from core.registry import registry


def pareto_tail_estimator(context):
    """
    Institutional Pareto Tail Index (MLE)

    - Uses cost-adjusted net returns
    - Adaptive extreme-loss threshold
    - Measures loss-tail thickness
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 100:
        return None

    losses = -returns[returns < 0]

    if losses.size < 30:
        return None

    losses = np.sort(losses)

    k = max(20, int(losses.size * 0.05))
    tail = losses[-k:]

    x_min = tail[0]

    if x_min <= 0:
        return None

    alpha = 1 + k / np.sum(np.log(tail / x_min))

    return float(alpha)


registry.register(
    "pareto_tail_estimator",
    pareto_tail_estimator,
    category="distributions",
    dependencies=["student_t_fit"]
)