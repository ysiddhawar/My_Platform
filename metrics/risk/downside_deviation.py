import numpy as np
from core.registry import registry


def downside_deviation(context):
    """
    Institutional Downside Deviation

    - Uses cost-adjusted net returns
    - Adaptive target threshold
    - Used by Sortino / Survival layer
    """

    returns = context.get_cache("net_returns")

    if returns is None or returns.size < 20:
        return None

    target = np.median(returns)

    downside = returns[returns < target]

    if downside.size == 0:
        return 0.0

    deviation = np.sqrt(np.mean((downside - target) ** 2))

    return float(deviation)


registry.register(
    "downside_deviation",
    downside_deviation,
    category="risk",
    dependencies=["adjusted_pnl"]
)