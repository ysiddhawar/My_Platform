import numpy as np
from core.registry import registry


def tail_ratio(context):
    """
    Institutional Tail Asymmetry Diagnostic

    - Uses cached net return distribution
    - Compares upper vs lower extreme magnitude
    - >1 = stronger upside tail
    - <1 = heavier downside tail
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 50:
        return None

    lower_pct = 5
    upper_pct = 95

    lower_tail = np.percentile(returns, lower_pct)
    upper_tail = np.percentile(returns, upper_pct)

    if abs(lower_tail) < 1e-12:
        return None

    ratio = abs(upper_tail) / abs(lower_tail)

    return float(ratio)


registry.register(
    "tail_ratio",
    tail_ratio,
    category="distributions",
    dependencies=["normality_test"]
)