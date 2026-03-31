import numpy as np
from core.registry import registry


def block_bootstrap(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 30:
        return None

    n_sims = max(300, int(np.sqrt(n)*20))
    block  = max(5, int(np.sqrt(n)))

    sims = []

    for _ in range(n_sims):

        path = []

        while len(path) < n:

            start = np.random.randint(0, n-block)
            path.extend(returns[start:start+block])

        path = np.asarray(path[:n])

        sims.append(np.prod(1+path)-1)

    sims = np.asarray(sims)

    return {
        "median": float(np.median(sims)),
        "worst_5": float(np.percentile(sims,5)),
        "worst_1": float(np.percentile(sims,1)),
        "best_95": float(np.percentile(sims,95))
    }


registry.register(
    "block_bootstrap",
    block_bootstrap,
    category="robustness",
    dependencies=["adjusted_pnl"]
)