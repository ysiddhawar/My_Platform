# survival/risk_of_ruin.py

import numpy as np
import math
from core.registry import registry


def risk_of_ruin(context):
    """
    Institutional Risk-of-Ruin Estimator

    Computes:
        probability capital hits ruin floor
        under execution-adjusted returns

    Outputs:
        ruin_probability
        expected_time_to_ruin

    Dependencies:
        execution_impact_model
        deployable_leverage
    """

    impact_path = context.get_cache("impact_adjusted_returns")
    leverage = context.get_result("deployable_leverage")

    if impact_path is None or leverage is None:
        return None

    r = np.asarray(impact_path, dtype=np.float64)

    if r.size < 50 or not np.isfinite(r).all():
        return None

    if isinstance(leverage, dict):
        lev = leverage.get("max_safe_leverage", 1.0)
    else:
        lev = float(leverage)

    r = r * lev

    mu = np.mean(r)
    sigma = np.std(r)

    if sigma <= 0:
        return None

    ruin_floor = context.data.get("ruin_floor", 0.2)

    z = (np.log(ruin_floor) - mu * r.size) / (sigma * np.sqrt(r.size))

    ruin_prob = 0.5 * (1 + math.erf(z / np.sqrt(2)))

    expected_time = None
    if ruin_prob > 0:
        expected_time = r.size * (1 - ruin_prob)

    return {
        "ruin_probability": float(ruin_prob),
        "expected_time_to_ruin": float(expected_time) if expected_time else None
    }


registry.register(
    "risk_of_ruin",
    risk_of_ruin,
    category="survival",
    dependencies=[
        "execution_impact_model",
        "deployable_leverage"
    ]
)