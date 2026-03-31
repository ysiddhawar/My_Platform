import numpy as np
from core.registry import registry


def regime_switching(context):
    """
    Detects regime change frequency
    and duration statistics.
    """

    vr = context.get_result("volatility_regime")

    if vr is None:
        return None

    regimes = vr["regime_series"]

    if len(regimes) < 20:
        return None

    durations = []
    current = regimes[0]
    count = 1

    for r in regimes[1:]:
        if r == current:
            count += 1
        else:
            durations.append(count)
            current = r
            count = 1

    durations.append(count)

    return {
        "regime_changes": int(len(durations) - 1),
        "avg_duration": float(np.mean(durations)),
        "max_duration": int(np.max(durations)),
        "min_duration": int(np.min(durations))
    }


registry.register(
    "regime_switching",
    regime_switching,
    category="regimes",
    dependencies=["volatility_regime"]
)