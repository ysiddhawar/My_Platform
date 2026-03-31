import numpy as np
from scipy import stats
from core.registry import registry


def noise_stability(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 50:
        return None

    base = np.std(returns)
    noise_levels = np.linspace(0, base*0.5, 5)
    sims = max(50, int(np.sqrt(n)))

    mu0 = np.mean(returns)
    sd0 = np.std(returns, ddof=1)

    baseline = mu0/sd0 if sd0>0 else 0

    degradation = []

    for nl in noise_levels:

        sharpe_list = []

        for _ in range(sims):

            noise = stats.t.rvs(df=5,size=n)*nl
            noisy = returns + noise

            mu = np.mean(noisy)
            sd = np.std(noisy,ddof=1)

            if sd>0:
                sharpe_list.append(mu/sd)

        if sharpe_list:
            degradation.append(np.mean(sharpe_list))

    if not degradation:
        return None

    degradation = np.asarray(degradation)

    return {
        "baseline_sharpe": float(baseline),
        "mean_degraded_sharpe": float(np.mean(degradation)),
        "max_degradation": float(baseline-np.min(degradation)),
        "stability_ratio": float(np.mean(degradation>0))
    }


registry.register(
    "noise_stability",
    noise_stability,
    category="robustness",
    dependencies=["adjusted_pnl"]
)