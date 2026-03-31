# survival/fragility_score.py

import numpy as np
from core.registry import registry


def fragility_score(context):
    """
    Institutional System Fragility Estimator

    Converts deployment stress surface into:
        system_fragility ∈ [0, 1]

    Uses:
        - crash drawdown
        - liquidity stress
        - execution impact stress
        - regime collapse
        - correlation breakdown

    Properties:
        - convex DD sensitivity
        - bounded response
        - finite-safe aggregation
        - deployability-weighted

    Dependencies:
        stress_engine
    """

    stress = context.get_result("stress_engine")

    if stress is None:
        return None

    keys = [
        "crash_dd",
        "liquidity_dd",
        "execution_impact_dd",
        "regime_dd",
        "corr_regime_dd"
    ]

    dd_vec = []

    for k in keys:
        v = stress.get(k)
        if v is not None and np.isfinite(v):
            dd_vec.append(abs(v))

    if len(dd_vec) < 2:
        return None

    dd_vec = np.clip(np.array(dd_vec), 0.0, 1.0)

    # Convex sensitivity (institutional risk aversion)
    gamma = context.data.get("fragility_convexity", 2.5)
    convex = dd_vec ** gamma

    # Deployment weighting
    w = np.array([
        0.30,   # crash
        0.20,   # liquidity
        0.25,   # execution impact
        0.15,   # regime
        0.10    # correlation
    ])[:len(convex)]

    w = w / np.sum(w)

    agg = np.sum(w * convex)

    # Bounded nonlinear squashing
    frag = 1.0 - np.exp(-agg)

    frag = float(np.clip(frag, 0.0, 1.0))

    context.set_cache("system_fragility", frag)

    return frag


registry.register(
    "fragility_score",
    fragility_score,
    category="survival",
    dependencies=[
        "stress_engine"
    ]
)