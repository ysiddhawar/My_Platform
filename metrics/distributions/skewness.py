import numpy as np
from scipy import stats
from core.registry import registry


def skewness(context):

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 30:
        return None

    skew = stats.skew(returns, bias=False)

    return float(skew)


registry.register(
    "skewness",
    skewness,
    category="distributions",
    dependencies=["normality_test"]
)