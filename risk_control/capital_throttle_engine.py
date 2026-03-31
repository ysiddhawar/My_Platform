# risk_control/capital_throttle_engine.py

import numpy as np
from core.registry import registry


def capital_throttle_engine(context):
    """
    Survival-Aware Deployable Capital Engine

    Converts:

        Ideal Allocation
        × Runtime Throttle
        × Survival Policy
        × Safe Leverage Cap

    Into:

        Deployable Capital Per Strategy
    """

    base_alloc = context.get_result("capital_engine")
    runtime_throttle = context.get_result("dynamic_throttle")
    survival_policy = context.get_result("capital_throttle_policy")
    leverage_cap = context.get_result("deployable_leverage")

    total_capital = context.data.get("total_capital", 1_000_000)

    if base_alloc is None:
        return None

    if runtime_throttle is None:
        runtime_throttle = 1.0

    if survival_policy is None:
        survival_policy = 1.0

    if leverage_cap is None:
        leverage_cap = 1.0

    keys = list(base_alloc.keys())

    weights = np.array(
        [base_alloc[k] for k in keys],
        dtype=np.float64
    )

    if (
        not np.isfinite(weights).all() or
        np.sum(weights) == 0
    ):
        return None

    weights = weights / np.sum(weights)

    # -------------------------------------
    # Deployable Capital Fraction
    # -------------------------------------
    deployable_fraction = (
        float(runtime_throttle) *
        float(survival_policy) *
        float(leverage_cap)
    )

    deployable_fraction = float(
        np.clip(deployable_fraction, 0.01, 1.0)
    )

    deployable_capital = total_capital * deployable_fraction

    # -------------------------------------
    # Strategy Capital Allocation
    # -------------------------------------
    strategy_capital = weights * deployable_capital

    throttled_alloc = dict(
        zip(keys, strategy_capital.tolist())
    )

    context.set_cache(
        "deployable_capital",
        deployable_capital
    )

    context.set_cache(
        "deployable_fraction",
        deployable_fraction
    )

    return throttled_alloc


registry.register(
    "capital_throttle_engine",
    capital_throttle_engine,
    category="risk_control",
    dependencies=[
        "capital_engine",
        "dynamic_throttle",
        "capital_throttle_policy",
        "deployable_leverage"
    ]
)