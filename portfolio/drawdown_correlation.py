import numpy as np
from core.registry import registry


def drawdown_correlation(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    equity = np.cumprod(1 + R, axis=0)
    peaks = np.maximum.accumulate(equity, axis=0)
    dd = (equity - peaks) / peaks

    corr = np.corrcoef(dd, rowvar=False)

    return {
        "strategies": names,
        "drawdown_correlation_matrix": corr.tolist()
    }


registry.register(
    "drawdown_correlation",
    drawdown_correlation,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)