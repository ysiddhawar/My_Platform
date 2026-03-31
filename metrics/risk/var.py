import numpy as np
from scipy import stats
from core.registry import registry


def value_at_risk(context):
    """
    Institutional Distribution-Aware VaR

    - Uses cost-adjusted net returns
    - Auto selects tail model
    - Student-t aware
    """

    returns = context.get_cache("net_returns")

    if returns is None or returns.size < 30:
        return None

    alpha = 0.05

    kurt = stats.kurtosis(returns, fisher=True)

    if kurt > 1:

        df, loc, scale = stats.t.fit(returns)

        var = stats.t.ppf(alpha, df, loc=loc, scale=scale)

    else:

        var = np.percentile(returns, alpha * 100)

    return float(var)


registry.register(
    "value_at_risk",
    value_at_risk,
    category="risk",
    dependencies=["adjusted_pnl"]
)