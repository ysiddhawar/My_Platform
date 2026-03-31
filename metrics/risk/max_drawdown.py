import numpy as np
from core.registry import registry


def max_drawdown(context):
    """
    Institutional Max Drawdown

    Uses:
    - cost-adjusted net return stream
    - compounded equity curve
    """

    returns = context.get_cache("net_returns")
    if returns is None:
        returns = context.get_cache("clean_returns")
    if returns is None:
        returns = np.asarray(
            context.data.get("returns", []),
            dtype=np.float64
        )
        returns = returns[~np.isnan(returns)]

    if returns is None or returns.size < 2:
        return None

    equity = np.cumprod(1 + returns)

    peaks = np.maximum.accumulate(equity)

    drawdowns = (equity - peaks) / peaks

    return float(np.min(drawdowns))


registry.register(
    "max_drawdown",
    max_drawdown,
    category="risk",
    dependencies=["adjusted_pnl"]
)