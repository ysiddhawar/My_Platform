# survival/deployable_leverage.py

import numpy as np
from core.registry import registry


def deployable_leverage(context):
    """
    Institutional Deployable Leverage Estimator

    Converts:
        system_fragility
        execution_impact_dd
        liquidity_dd
        worst_case_dd

    Into:
        max_safe_leverage

    Guarantees:
        - bounded leverage
        - convex fragility penalty
        - execution-capacity decay
        - liquidity-aware reduction

    Dependencies:
        fragility_score
        stress_engine
    """

    frag = context.get_result("fragility_score")
    stress = context.get_result("stress_engine")

    if frag is None or stress is None:
        return None

    impact_dd = stress.get("execution_impact_dd", 0.0)
    liq_dd = stress.get("liquidity_dd", 0.0)
    worst_dd = stress.get("worst_case_dd", 0.0)

    if not all(map(np.isfinite, [frag, impact_dd, liq_dd, worst_dd])):
        return None

    frag = np.clip(frag, 0.0, 1.0)

    # -----------------------------------------
    # Institutional decay model
    # -----------------------------------------
    frag_penalty = np.exp(-3.0 * frag)

    impact_penalty = 1.0 / (1.0 + abs(impact_dd))
    liquidity_penalty = 1.0 / (1.0 + abs(liq_dd))

    survival_capacity = frag_penalty * impact_penalty * liquidity_penalty

    base_leverage = context.data.get("base_leverage_cap", 5.0)

    max_leverage = base_leverage * survival_capacity

    max_leverage = float(np.clip(max_leverage, 0.1, base_leverage))

    context.set_cache("max_safe_leverage", max_leverage)

    return max_leverage


registry.register(
    "deployable_leverage",
    deployable_leverage,
    category="survival",
    dependencies=[
        "fragility_score",
        "stress_engine"
    ]
)