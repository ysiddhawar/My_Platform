import numpy as np
from scipy import stats
from core.registry import registry


def kurtosis(context):

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 30:
        return None

    kurt = stats.kurtosis(returns, fisher=True, bias=False)

    return float(kurt)


registry.register(
    "kurtosis",
    kurtosis,
    category="distributions",
    dependencies=["normality_test"]
)