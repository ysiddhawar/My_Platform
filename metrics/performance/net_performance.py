import numpy as np
from core.registry import registry


def net_sharpe(context):
    """
    Net Sharpe Ratio (Post-Cost)

    Uses net return stream after:
    - brokerage
    - slippage
    - swap
    - execution fees

    Downstream of:
    adjusted_pnl → net_returns
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    n = returns.size
    if n < 30:
        return None

    mean = np.mean(returns)
    std = np.std(returns, ddof=1)

    if std == 0:
        return None

    if n > 5000:
        annual_factor = np.sqrt(252 * 6.5 * 60)
    elif n > 1000:
        annual_factor = np.sqrt(252 * 6.5)
    else:
        annual_factor = np.sqrt(252)

    return float((mean / std) * annual_factor)


registry.register(
    "net_sharpe",
    net_sharpe,
    category="performance",
    dependencies=["adjusted_pnl"]
)


# ---------------------------------------------------------


def net_cagr(context):
    """
    Net CAGR (Post-Cost)

    Uses cost-adjusted net returns
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

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
    "net_cagr",
    net_cagr,
    category="performance",
    dependencies=["adjusted_pnl"]
)


# ---------------------------------------------------------


def net_sortino(context):
    """
    Net Sortino Ratio (Post-Cost)

    Uses downside volatility of net returns
    """

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    downside = returns[returns < 0]

    if downside.size < 5:
        return None

    downside_std = np.std(downside, ddof=1)

    if downside_std == 0:
        return None

    mean = np.mean(returns)

    n = returns.size

    if n > 5000:
        annual_factor = np.sqrt(252 * 6.5 * 60)
    elif n > 1000:
        annual_factor = np.sqrt(252 * 6.5)
    else:
        annual_factor = np.sqrt(252)

    return float((mean / downside_std) * annual_factor)


registry.register(
    "net_sortino",
    net_sortino,
    category="performance",
    dependencies=["adjusted_pnl"]
)