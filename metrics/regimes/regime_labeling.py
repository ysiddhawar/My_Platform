import numpy as np
from core.registry import registry


def regime_labeling(context):
    """
    Regime Labeling Engine

    - Labels each time index LOW / MEDIUM / HIGH
    - Based on adaptive rolling volatility
    """

    vr = context.get_result("volatility_regime")

    if vr is None:
        return None

    return {
        "window": vr["window"],
        "low_threshold": vr["low_threshold"],
        "high_threshold": vr["high_threshold"],
        "regimes": vr["regime_series"]
    }


registry.register(
    "regime_labeling",
    regime_labeling,
    category="regimes",
    dependencies=["volatility_regime"]
)