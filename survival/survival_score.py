# survival/survival_score.py

import numpy as np
from core.registry import registry


def survival_score(context):
    """
    Institutional Survival Score Aggregator

    Converts:
        ruin probability
        capital decay
        fragility score

    Into:
        deployable survival score ∈ [0,1]

    Dependencies:
        ruin_probability_mc
        capital_decay
        fragility_score
    """

    mc = context.get_result("ruin_probability_mc")
    decay = context.get_result("capital_decay")
    frag = context.get_result("fragility_score")

    if mc is None or decay is None or frag is None:
        return None

    if isinstance(mc, dict):
        ruin = mc.get("mc_ruin_probability", 0.0)
    else:
        ruin = float(mc)

    if isinstance(decay, dict):
        decay_rate = decay.get("capital_decay_rate", 0.0)
    else:
        decay_rate = float(decay)

    if isinstance(frag, dict):
        fragility = frag.get("system_fragility", frag.get("fragility_score", 0.0))
    else:
        fragility = float(frag)

    score = 1 - (
        0.4 * ruin +
        0.3 * decay_rate +
        0.3 * fragility
    )

    score = np.clip(score, 0.0, 1.0)

    return float(score)


registry.register(
    "survival_score",
    survival_score,
    category="survival",
    dependencies=[
        "ruin_probability_mc",
        "capital_decay",
        "fragility_score"
    ]
)