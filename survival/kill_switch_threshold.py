# survival/kill_switch_threshold.py

import numpy as np
from core.registry import registry


def kill_switch_threshold(context):
    """
    Institutional Kill-Switch Policy

    Uses:
        - system_fragility
        - correlation regime collapse
        - worst-case drawdown

    Outputs:
        kill_triggered (bool)

    Properties:
        - deployability-aware
        - convex fragility sensitivity
        - correlation collapse gating

    Dependencies:
        fragility_score
        stress_engine
    """

    frag = context.get_result("fragility_score")
    stress = context.get_result("stress_engine")

    if frag is None or stress is None:
        return None

    corr_dd = stress.get("corr_regime_dd", 0.0)
    worst_dd = stress.get("worst_case_dd", 0.0)

    if not all(map(np.isfinite, [frag, corr_dd, worst_dd])):
        return None

    frag = np.clip(frag, 0.0, 1.0)

    # -----------------------------------------
    # Composite collapse index
    # -----------------------------------------
    collapse_index = (
        0.5 * frag
        + 0.3 * abs(corr_dd)
        + 0.2 * abs(worst_dd)
    )

    threshold = context.data.get(
        "kill_fragility_threshold",
        0.65
    )

    kill = collapse_index >= threshold

    return {
        "collapse_index": float(collapse_index),
        "threshold": float(threshold),
        "kill_triggered": bool(kill)
    }


registry.register(
    "kill_switch_threshold",
    kill_switch_threshold,
    category="survival",
    dependencies=[
        "fragility_score",
        "stress_engine"
    ]
)