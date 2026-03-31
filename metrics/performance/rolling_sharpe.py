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


def rolling_sharpe(context):

    returns = _get_research_returns(context)

    n = returns.size
    if n < 20:
        return None

    window = max(10, int(n * 0.05))

    sharpes = []

    for i in range(n - window + 1):

        chunk = returns[i:i+window]
        std = np.std(chunk, ddof=1)

        if std == 0:
            sharpes.append(0.0)
        else:
            sharpes.append(np.mean(chunk) / std)

    return np.array(sharpes)


registry.register(
    "rolling_sharpe",
    rolling_sharpe,
    category="performance",
    dependencies=["adjusted_pnl"]
)