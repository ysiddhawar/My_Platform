# survival/survival_engine.py

import numpy as np
from core.registry import registry


def survival_engine(context):
    """
    Institutional Survival Aggregator

    Combines:
        - Impact-adjusted path
        - Deployable leverage
        - Capital decay
        - MC ruin probability
        - Fragility score

    Into:
        Institutional survivability classification
        Deployability-grade survival score

    Dependencies:
        execution_impact_model
        deployable_leverage
        capital_decay
        ruin_probability_mc
        survival_score
    """

    impact_path = context.get_cache("impact_adjusted_returns")
    lev = context.get_result("deployable_leverage")
    decay = context.get_result("capital_decay")
    mc = context.get_result("ruin_probability_mc")
    surv = context.get_result("survival_score")

    if (
        impact_path is None or
        lev is None or
        decay is None or
        mc is None or
        surv is None
    ):
        return None

    r = np.asarray(impact_path, dtype=np.float64)

    if r.size < 50 or not np.isfinite(r).all():
        return None

    if isinstance(lev, dict):
        leverage = lev.get("max_safe_leverage", 1.0)
    else:
        leverage = float(lev)

    if isinstance(decay, dict):
        decay_rate = decay.get("capital_decay_rate", 0.0)
    else:
        decay_rate = float(decay)

    if isinstance(mc, dict):
        ruin_prob = mc.get("mc_ruin_probability", 1.0)
    else:
        ruin_prob = float(mc)

    if isinstance(surv, dict):
        survival = float(surv.get("survival_score", 0.0))
    else:
        survival = float(surv)

    # -----------------------------------------
    # Capital Evolution Under Deployment
    # -----------------------------------------
    deployed = r * leverage * (1 - decay_rate)

    equity = np.cumprod(1 + deployed)

    peaks = np.maximum.accumulate(equity)
    dd = (equity - peaks) / peaks

    worst_dd = np.min(dd)

    # -----------------------------------------
    # Institutional Survival Grading
    # -----------------------------------------
    if survival > 0.95 and ruin_prob < 0.01:
        grade = "INSTITUTIONAL"
    elif survival > 0.85 and ruin_prob < 0.05:
        grade = "ACCEPTABLE"
    elif survival > 0.70:
        grade = "FRAGILE"
    else:
        grade = "NON-DEPLOYABLE"

    return {
        "deployable_survival_score": float(survival),
        "probability_of_ruin": float(ruin_prob),
        "ruin_probability": float(ruin_prob),
        "capital_decay_rate": float(decay_rate),
        "deployment_drawdown": float(worst_dd),
        "survival_grade": grade
    }


registry.register(
    "survival_engine",
    survival_engine,
    category="survival",
    dependencies=[
        "execution_impact_model",
        "deployable_leverage",
        "capital_decay",
        "ruin_probability_mc",
        "survival_score"
    ]
)