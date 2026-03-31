import numpy as np
from scipy.stats import t
from core.registry import registry


def _get_research_returns(context):

    cached = context.get_cache("net_returns")
    if cached is not None:
        return cached

    returns = np.asarray(
        context.data.get("returns", []),
        dtype=np.float64
    )

    returns = returns[~np.isnan(returns)]
    context.set_cache("clean_returns", returns)

    return returns


def sharpe(context):

    returns = _get_research_returns(context)

    n = returns.size
    if n < 30:
        return None

    mean = np.mean(returns)
    std = np.std(returns, ddof=1)

    if std == 0:
        return 0.0

    try:
        df, loc, scale = t.fit(returns)
        tail_adj = np.sqrt((df - 2) / df) if df > 2 else 1.0
    except Exception:
        tail_adj = 1.0

    sr = (mean / std) * tail_adj

    if n > 5000:
        annual = np.sqrt(252 * 6.5 * 60)
    elif n > 1000:
        annual = np.sqrt(252 * 6.5)
    else:
        annual = np.sqrt(252)

    return float(sr * annual)


registry.register(
    "sharpe",
    sharpe,
    category="performance",
    dependencies=["adjusted_pnl"]
)