import numpy as np
from scipy import stats
from core.registry import registry


def _get_clean_net_returns(context):

    cached = context.get_cache("dist_clean_returns")

    if cached is not None:
        return cached

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    clean = returns[~np.isnan(returns)]

    context.set_cache("dist_clean_returns", clean)

    return clean


def normality_test(context):

    returns = _get_clean_net_returns(context)

    if returns is None or returns.size < 30:
        return None

    n = returns.size

    if n < 5000:
        sw_stat, sw_p = stats.shapiro(returns)
    else:
        sw_stat, sw_p = None, None

    jb_stat, jb_p = stats.jarque_bera(returns)

    return {
        "jarque_bera_stat": float(jb_stat),
        "jarque_bera_pvalue": float(jb_p),
        "shapiro_stat": float(sw_stat) if sw_stat else None,
        "shapiro_pvalue": float(sw_p) if sw_p else None,
        "is_normal_distribution": bool(jb_p > 0.05)
    }


registry.register(
    "normality_test",
    normality_test,
    category="distributions",
    dependencies=["adjusted_pnl"]
)