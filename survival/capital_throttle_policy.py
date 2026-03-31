# survival/capital_throttle_policy.py

import numpy as np
from core.registry import registry


def capital_throttle_policy(context):
    """
    Institutional Capital Deployment Policy

    Converts:
        system_fragility
        drawdown_percentile
        max_safe_leverage

    Into:
        throttle_factor ∈ [0,1]

    Meaning:
        real-time capital deployment %
    """

    frag = context.get_result("fragility_score")
    dd_pct = context.get_result("drawdown_percentile")
    lev = context.get_result("deployable_leverage")

    if frag is None or dd_pct is None or lev is None:
        return None

    if not all(map(np.isfinite, [frag, dd_pct, lev])):
        return None

    frag = np.clip(frag, 0.0, 1.0)
    dd_pct = np.clip(dd_pct, 0.0, 1.0)

    # -----------------------------------------
    # Institutional convex throttle decay
    # -----------------------------------------
    frag_decay = np.exp(-2.5 * frag)
    stress_decay = np.exp(-2.0 * dd_pct)

    leverage_norm = lev / context.data.get(
        "base_leverage_cap",
        5.0
    )

    throttle = frag_decay * stress_decay * leverage_norm

    throttle = float(np.clip(throttle, 0.05, 1.0))

    context.set_cache("capital_throttle_factor", throttle)

    return throttle


registry.register(
    "capital_throttle_policy",
    capital_throttle_policy,
    category="survival",
    dependencies=[
        "fragility_score",
        "drawdown_percentile",
        "deployable_leverage"
    ]
)