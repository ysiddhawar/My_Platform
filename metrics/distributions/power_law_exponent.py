import numpy as np
from core.registry import registry


def power_law_exponent(context):
    """
    Institutional Power-Law Tail Exponent

    - Uses cost-adjusted net return distribution
    - Adaptive extreme-loss threshold
    - Hill estimator for crash-tail decay
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

    logs = np.log(tail / threshold)
    hill = np.mean(logs)

    if hill <= 0:
        return None

    alpha = 1 / hill

    return {
        "power_law_alpha": float(alpha),
        "tail_threshold": float(threshold),
        "tail_size": int(tail.size)
    }


registry.register(
    "power_law_exponent",
    power_law_exponent,
    category="distributions",
    dependencies=["student_t_fit"]
)