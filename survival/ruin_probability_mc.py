# survival/ruin_probability_mc.py

import numpy as np
from core.registry import registry


def ruin_probability_mc(context):
    """
    Institutional Monte Carlo Risk-of-Ruin Model

    Pathwise survival estimation using:
        execution-adjusted returns
        deployable leverage
        stress-driven decay

    Outputs:
        mc_ruin_probability
        median_survival_time

    Dependencies:
        execution_impact_model
        deployable_leverage
    """

    r = context.get_cache("impact_adjusted_returns")
    lev = context.get_result("deployable_leverage")

    if r is None or lev is None:
        return None

    r = np.asarray(r, dtype=np.float64)

    if r.size < 50 or not np.isfinite(r).all():
        return None

    if isinstance(lev, dict):
        leverage = lev.get("max_safe_leverage", 1.0)
    else:
        leverage = float(lev)

    sims = context.data.get("ruin_mc_sims", 500)
    ruin_floor = context.data.get("ruin_floor", 0.2)

    T = r.size
    ruin_count = 0
    survival_times = []

    for _ in range(sims):

        path = np.random.choice(r, size=T, replace=True)
        path = path * leverage

        equity = np.cumprod(1 + path)

        ruin_idx = np.where(equity < ruin_floor)[0]

        if ruin_idx.size > 0:
            ruin_count += 1
            survival_times.append(ruin_idx[0])
        else:
            survival_times.append(T)

    ruin_prob = ruin_count / sims
    median_time = np.median(survival_times)

    return {
        "mc_ruin_probability": float(ruin_prob),
        "median_survival_time": float(median_time)
    }


registry.register(
    "ruin_probability_mc",
    ruin_probability_mc,
    category="survival",
    dependencies=[
        "execution_impact_model",
        "deployable_leverage"
    ]
)