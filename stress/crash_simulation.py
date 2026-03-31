import numpy as np
from scipy import stats
from core.registry import registry


def crash_simulation(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    n_assets, T = R.shape

    if T < 50:
        return None

    results = {}

    simulations = 500

    for i, name in enumerate(keys):

        r = R[i]

        try:
            df, loc, scale = stats.t.fit(r)
        except Exception:
            continue

        shock = stats.t.ppf(0.01, df, loc=loc, scale=scale)

        losses = []

        for _ in range(simulations):

            sim = stats.t.rvs(df, loc=loc, scale=scale, size=T)

            idx = np.random.randint(0, T)
            sim[idx] = shock

            equity = np.cumprod(1 + sim)
            peak = np.maximum.accumulate(equity)
            dd = (equity - peak) / peak
            losses.append(np.min(dd))

        losses = np.array(losses)

        results[name] = {
            "worst_case_drawdown": float(np.min(losses)),
            "avg_drawdown": float(np.mean(losses)),
            "prob_ruin_50pct": float(np.mean(losses < -0.5))
        }

    return results


registry.register(
    "crash_simulation",
    crash_simulation,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)