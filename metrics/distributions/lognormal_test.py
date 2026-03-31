import numpy as np
from scipy import stats
from core.registry import registry


def lognormal_test(context):
    """
    Lognormal Price Path Test

    - Builds equity path from net returns
    - Tests log(price) ~ Normal
    - KS goodness-of-fit
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 50:
        return None

    equity = np.cumprod(1 + returns)
    equity = equity[equity > 0]

    if equity.size < 50:
        return None

    log_price = np.log(equity)

    mu = np.mean(log_price)
    sigma = np.std(log_price, ddof=1)

    try:
        ks_stat, p_value = stats.kstest(
            log_price,
            'norm',
            args=(mu, sigma)
        )
    except Exception:
        return None

    return {
        "lognormal_ks_stat": float(ks_stat),
        "lognormal_p_value": float(p_value),
        "log_mu": float(mu),
        "log_sigma": float(sigma)
    }


registry.register(
    "lognormal_test",
    lognormal_test,
    category="distributions",
    dependencies=["adjusted_pnl"]
)