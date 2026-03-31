import numpy as np
from core.registry import registry


def equity_curve(context):

    cached = context.get_cache("net_returns")
    if cached is not None:
        returns = cached
    else:
        returns = np.asarray(
            context.data.get("returns", []),
            dtype=np.float64
        )
        returns = returns[~np.isnan(returns)]

    if returns.size == 0:
        return None

    equity = np.cumprod(1.0 + returns)

    context.set_cache("equity_curve", equity)
    return equity


registry.register(
    "equity_curve",
    equity_curve,
    category="performance",
    dependencies=["adjusted_pnl"]
)