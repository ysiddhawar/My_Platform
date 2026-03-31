# risk_control/throttle.py

import numpy as np
from core.registry import registry


def dynamic_throttle(context):
    """
    Survival-Aware Runtime Deployment Throttle

    Produces:
        throttle_factor ∈ [0,1]

    Uses:
        - Runtime equity DD
        - Volatility expansion
        - System fragility
        - Survival deployment policy
        - Kill pre-trigger clamp
    """

    equity = context.get_result("equity_curve")
    rolling_vol = context.get_result("rolling_volatility")
    fragility = context.get_result("fragility_score")
    throttle_policy = context.get_result("capital_throttle_policy")
    kill = context.get_result("kill_switch_threshold")

    max_dd_limit = context.data.get("max_drawdown_limit", 0.20)

    if (
        equity is None or
        rolling_vol is None or
        fragility is None or
        throttle_policy is None
    ):
        return 1.0

    equity = np.asarray(equity, dtype=np.float64)
    rolling_vol = np.asarray(rolling_vol, dtype=np.float64)

    if (
        equity.size < 30 or
        not np.isfinite(equity).all() or
        not np.isfinite(rolling_vol).all()
    ):
        return 1.0

    # -------------------------------------
    # Runtime Drawdown Pressure
    # -------------------------------------
    peaks = np.maximum.accumulate(equity)
    dd = (equity - peaks) / (peaks + 1e-12)
    current_dd = abs(dd[-1])

    dd_pressure = min(current_dd / max_dd_limit, 1.0)

    # -------------------------------------
    # Volatility Expansion Pressure
    # -------------------------------------
    if rolling_vol.size > 5:
        vol_ratio = rolling_vol[-1] / (np.mean(rolling_vol) + 1e-12)
        vol_pressure = max(min(vol_ratio, 2.0) - 1.0, 0.0)
    else:
        vol_pressure = 0.0

    # -------------------------------------
    # Fragility Pressure
    # -------------------------------------
    try:
        frag_pressure = min(float(fragility), 1.0)
    except Exception:
        frag_pressure = 0.0

    # -------------------------------------
    # Kill Pre-Trigger Clamp
    # -------------------------------------
    kill_clamp = 1.0
    if isinstance(kill, dict):
        if kill.get("kill_triggered", False):
            kill_clamp = 0.0

    # -------------------------------------
    # Convex Runtime Decay
    # -------------------------------------
    runtime_pressure = (
        0.5 * dd_pressure +
        0.25 * vol_pressure +
        0.25 * frag_pressure
    )

    runtime_decay = np.exp(-2.0 * runtime_pressure)

    # -------------------------------------
    # Final Throttle
    # -------------------------------------
    throttle = (
        float(throttle_policy) *
        runtime_decay *
        kill_clamp
    )

    throttle = float(np.clip(throttle, 0.01, 1.0))

    context.set_cache("runtime_throttle_factor", throttle)

    return throttle


registry.register(
    "dynamic_throttle",
    dynamic_throttle,
    category="risk_control",
    dependencies=[
        "equity_curve",
        "rolling_volatility",
        "fragility_score",
        "capital_throttle_policy",
        "kill_switch_threshold"
    ]
)