# survival/capital_decay.py

import numpy as np
from core.registry import registry


def capital_decay(context):
    """
    Institutional Capital Survival Decay Model

    Converts:
        stress-layer execution erosion
        liquidity drag
        regime drawdown pressure

    Into:
        deployable capital decay trajectory

    Outputs:
        capital_decay_rate
        effective_half_life
        survival_capital_ratio

    Dependencies:
        execution_impact_model
        drawdown_percentile
    """

    impact_path = context.get_cache("impact_adjusted_returns")
    dd_pct = context.get_result("drawdown_percentile")

    if impact_path is None or dd_pct is None:
        return None

    r = np.asarray(impact_path, dtype=np.float64)

    if r.size < 50 or not np.isfinite(r).all():
        return None

    # -------------------------------
    # Stress-adjusted capital path
    # -------------------------------
    equity = np.cumprod(1 + r)

    if not np.isfinite(equity).all():
        return None

    # terminal decay
    survival_ratio = equity[-1] / np.max(equity)

    # instantaneous erosion rate
    erosion = 1 - survival_ratio

    # drawdown pressure scaling
    if isinstance(dd_pct, dict):
        dd = dd_pct.get(
            "drawdown_percentile_95",
            dd_pct.get("drawdown_percentile", 0.0)
        )
    else:
        dd = float(dd_pct)

    decay_rate = erosion * (1 + abs(dd))

    # -------------------------------
    # Half-life estimation
    # -------------------------------
    lam = context.data.get("decay_lambda", 0.01)

    if lam <= 0:
        lam = 0.01

    half_life = np.log(2) / (lam + decay_rate)

    return {
        "capital_decay_rate": float(decay_rate),
        "effective_half_life": float(half_life),
        "survival_capital_ratio": float(survival_ratio)
    }


registry.register(
    "capital_decay",
    capital_decay,
    category="survival",
    dependencies=[
        "execution_impact_model",
        "drawdown_percentile"
    ]
)