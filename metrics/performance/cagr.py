import numpy as np
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


def cagr(context):

    returns = _get_research_returns(context)

    n = returns.size
    if n < 30:
        return None

    if n > 5000:
        periods = 252 * 6.5 * 60
    elif n > 1000:
        periods = 252 * 6.5
    else:
        periods = 252

    log_returns = np.log1p(returns)
    total_log = np.sum(log_returns)

    years = n / periods
    if years <= 0:
        return None

    return float(np.exp(total_log / years) - 1)


registry.register(
    "cagr",
    cagr,
    category="performance",
    dependencies=["adjusted_pnl"]
)