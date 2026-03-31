import numpy as np
from scipy import stats
from core.registry import registry


def conditional_var(context):
    """
    Institutional CVaR (Expected Shortfall)

    - Distribution-aware
    - Cost-adjusted net returns
    """

    returns = context.get_cache("net_returns")

    if returns is None or returns.size < 30:
        return None

    alpha = 0.05

    kurt = stats.kurtosis(returns, fisher=True)

    if kurt > 1:

        df, loc, scale = stats.t.fit(returns)

        q = stats.t.ppf(alpha, df)

        numerator = stats.t.pdf(q, df)
        es = loc - scale * (numerator / alpha) * ((df + q**2) / (df - 1))

    else:

        var = np.percentile(returns, alpha * 100)
        tail = returns[returns <= var]

        if tail.size == 0:
            return float(var)

        es = np.mean(tail)

    return float(es)


registry.register(
    "conditional_var",
    conditional_var,
    category="risk",
    dependencies=["adjusted_pnl"]
)