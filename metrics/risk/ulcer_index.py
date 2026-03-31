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

    equity = np.cumprod(1 + returns)
    peaks = np.maximum.accumulate(equity)

    drawdowns = (equity - peaks) / peaks

    squared_dd = drawdowns ** 2

    ui = np.sqrt(np.mean(squared_dd))

    return float(ui)


registry.register(
    "ulcer_index",
    ulcer_index,
    category="risk",
    dependencies=["adjusted_pnl"]
)