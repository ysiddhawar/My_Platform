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
        returns = returns[np.isfinite(returns)]

    returns = returns[np.isfinite(returns)]
    returns = returns[returns > -1.0]
    returns = np.clip(returns, -0.999, 10.0)

    if returns is None or returns.size < 2:
        return None

    equity = np.cumprod(1 + returns)
    equity = equity[np.isfinite(equity)]
    if equity.size < 2:
        return None

    peaks = np.maximum.accumulate(equity)
    peaks = np.where(peaks <= 0, np.nan, peaks)

    drawdowns = (equity - peaks) / peaks
    drawdowns = drawdowns[np.isfinite(drawdowns)]
    if drawdowns.size == 0:
        return None

    return float(np.min(drawdowns))


registry.register(
    "max_drawdown",
    max_drawdown,
    category="risk",
    dependencies=["adjusted_pnl"]
)
