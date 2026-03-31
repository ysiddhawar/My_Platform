import numpy as np
from core.registry import registry


def systemic_fragility(context):

    R = context.get_cache("strategy_returns")
    if R is None:
        return None

    T, N = R.shape
    if N < 2 or T < 50:
        return None

    # -----------------------------------------
    # Correlation Spike Risk
    # -----------------------------------------
    corr = np.corrcoef(R, rowvar=False)
    upper = corr[np.triu_indices_from(corr, k=1)]

    if len(upper) == 0:
        return None

    avg_corr = np.mean(np.abs(upper))

    # -----------------------------------------
    # Tail Dependency (Joint Loss Events)
    # -----------------------------------------
    thresholds = np.percentile(R, 5, axis=0)

    joint = 0
    for t in range(T):
        losses = np.sum(R[t] <= thresholds)
        if losses >= max(2, int(0.3 * N)):
            joint += 1

    tail_dep = joint / T

    # -----------------------------------------
    # Drawdown Synchronization
    # -----------------------------------------
    equity = np.cumprod(1 + R, axis=0)
    peaks = np.maximum.accumulate(equity, axis=0)
    dd = (equity - peaks) / peaks

    dd_corr = np.corrcoef(dd, rowvar=False)
    dd_upper = dd_corr[np.triu_indices_from(dd_corr, k=1)]

    avg_dd = np.mean(np.abs(dd_upper))

    frag = avg_corr + tail_dep + avg_dd

    return {
        "avg_correlation": float(avg_corr),
        "tail_dependency_ratio": float(tail_dep),
        "drawdown_correlation": float(avg_dd),
        "systemic_fragility_score": float(frag)
    }


registry.register(
    "systemic_fragility",
    systemic_fragility,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)