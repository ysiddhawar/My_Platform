import numpy as np
from scipy import stats
from core.registry import registry


def stress_scenarios(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    n_assets, T = R.shape

    if T < 50:
        return None

    simulations = context.data.get("stress_mc_sims", 500)
    shock_pct = context.data.get("stress_tail_pct", 1)

    results = {}

    for i, name in enumerate(keys):

        r = R[i]

        try:
            df, loc, scale = stats.t.fit(r)
        except Exception:
            continue

        shock = stats.t.ppf(shock_pct / 100, df, loc=loc, scale=scale)

        dd_list = []

        for _ in range(simulations):

            sim = stats.t.rvs(df, loc=loc, scale=scale, size=T)

            crash_idx = np.random.choice(T, size=2, replace=False)
            sim[crash_idx] = shock

            eq = np.cumprod(1 + sim)
            pk = np.maximum.accumulate(eq)
            dd = (eq - pk) / pk
            dd_list.append(np.min(dd))

        dd_arr = np.array(dd_list)

        results[name] = {
            "worst_case": float(np.min(dd_arr)),
            "median_case": float(np.median(dd_arr)),
            "tail_5pct": float(np.percentile(dd_arr, 5)),
            "ruin_probability_40pct": float(np.mean(dd_arr < -0.4))
        }

    return results


registry.register(
    "stress_scenarios",
    stress_scenarios,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)