# risk_control/kill_switch.py

import numpy as np
from core.registry import registry


def kill_switch(context):
    """
    Survival-Aware Institutional Runtime Kill-Switch

    Shutdown triggers:

        - Runtime drawdown breach
        - Drawdown velocity spike
        - Execution-capacity collapse
        - Runtime throttle collapse
        - Survival-engine ruin risk
        - Survival kill-threshold breach
    """

    aligned = context.get_cache("aligned_strategy_returns")
    weights = context.get_result("capital_engine")

    throttle = context.get_result("dynamic_throttle")
    leverage = context.get_result("deployable_leverage")
    survival = context.get_result("survival_engine")
    survival_kill = context.get_result("kill_switch_threshold")

    if aligned is None or weights is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    if R.shape[1] < 50:
        return None

    w = np.array(
        [weights[k] for k in keys],
        dtype=np.float64
    )

    if (
        not np.isfinite(w).all() or
        np.sum(w) == 0
    ):
        return None

    w = w / np.sum(w)

    # -------------------------------------
    # Portfolio Equity Path
    # -------------------------------------
    port_returns = np.sum(R.T * w, axis=1)

    equity = np.cumprod(1 + port_returns)
    peaks = np.maximum.accumulate(equity)
    dd = (equity - peaks) / (peaks + 1e-12)

    current_dd = abs(dd[-1])

    # -------------------------------------
    # Drawdown Velocity
    # -------------------------------------
    dd_velocity = 0.0

    if len(dd) > 5:
        dd_velocity = abs(dd[-1] - dd[-5])

    vel_limit = context.data.get(
        "kill_dd_velocity_limit", 0.05
    )

    vel_breach = dd_velocity > vel_limit

    # -------------------------------------
    # Adaptive DD Threshold
    # -------------------------------------
    dd_limit = context.data.get(
        "kill_dd_limit", 0.25
    )

    dd_breach = current_dd > dd_limit

    # -------------------------------------
    # Execution Capacity Collapse
    # -------------------------------------
    leverage_breach = (
        leverage is not None and
        leverage < 0.25
    )

    # -------------------------------------
    # Runtime Throttle Collapse
    # -------------------------------------
    throttle_breach = (
        throttle is not None and
        throttle < 0.25
    )

    # -------------------------------------
    # Survival Engine Ruin Risk
    # -------------------------------------
    ruin_breach = False

    if isinstance(survival, dict):
        ruin_prob = survival.get(
            "probability_of_ruin", 0.0
        )

        ruin_breach = ruin_prob > 0.10

    # -------------------------------------
    # Survival Threshold Breach
    # -------------------------------------
    survival_breach = (
        survival_kill is not None and
        survival_kill.get("kill_triggered", False)
    )

    # -------------------------------------
    # FINAL KILL SIGNAL
    # -------------------------------------
    kill = (
        dd_breach or
        vel_breach or
        leverage_breach or
        throttle_breach or
        ruin_breach or
        survival_breach
    )

    return {
        "kill_triggered": bool(kill),
        "current_drawdown": float(current_dd),
        "drawdown_velocity": float(dd_velocity),
        "drawdown_breach": bool(dd_breach),
        "velocity_breach": bool(vel_breach),
        "leverage_breach": bool(leverage_breach),
        "throttle_breach": bool(throttle_breach),
        "ruin_breach": bool(ruin_breach),
        "survival_breach": bool(survival_breach)
    }


registry.register(
    "kill_switch",
    kill_switch,
    category="risk_control",
    dependencies=[
        "portfolio_preprocessor",
        "capital_engine",
        "dynamic_throttle",
        "deployable_leverage",
        "survival_engine",
        "kill_switch_threshold"
    ]
)