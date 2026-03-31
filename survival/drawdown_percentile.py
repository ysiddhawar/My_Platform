# survival/drawdown_percentile.py

import numpy as np
from core.registry import registry


def drawdown_percentile(context):
    """
    Institutional Drawdown Surface Positioning

    Converts:
        stress_engine DD outputs

    Into:
        drawdown_percentile ∈ [0,1]

    Meaning:
        how extreme current deployable stress is
        relative to total stress surface

    Dependencies:
        stress_engine
    """

    stress = context.get_result("stress_engine")

    if stress is None:
        return None

    dd_vals = [
        stress.get("corr_regime_dd", 0.0),
        stress.get("crash_dd", 0.0),
        stress.get("liquidity_dd", 0.0),
        stress.get("scenario_dd", 0.0),
        stress.get("regime_dd", 0.0),
        stress.get("execution_impact_dd", 0.0)
    ]

    dd_vals = np.array(dd_vals, dtype=np.float64)

    if not np.isfinite(dd_vals).all():
        return None

    dd_vals = np.abs(dd_vals)

    worst = np.max(dd_vals)
    mean = np.mean(dd_vals)

    # convex stress percentile estimator
    percentile = worst / (worst + mean + 1e-8)

    percentile = float(np.clip(percentile, 0.0, 1.0))

    context.set_cache("drawdown_percentile", percentile)

    return percentile


registry.register(
    "drawdown_percentile",
    drawdown_percentile,
    category="survival",
    dependencies=[
        "stress_engine"
    ]
)