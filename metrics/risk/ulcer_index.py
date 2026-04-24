import numpy as np
from core.registry import registry


def ulcer_index(context):
    """
    Institutional Ulcer Index

    Measures:
    - depth of drawdowns
    - persistence of capital impairment

    Uses cost-adjusted net return stream.
    """

    returns = context.get_cache("net_returns")

    if returns is None or returns.size < 20:
        return None
    returns = returns[np.isfinite(returns)]
    returns = returns[returns > -1.0]
    returns = np.clip(returns, -0.999, 10.0)
    if returns.size < 20:
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

    squared_dd = drawdowns ** 2

    ui = np.sqrt(np.mean(squared_dd))

    return float(ui)


registry.register(
    "ulcer_index",
    ulcer_index,
    category="risk",
    dependencies=["adjusted_pnl"]
)
