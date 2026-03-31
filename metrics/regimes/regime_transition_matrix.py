import numpy as np
from core.registry import registry


def regime_transition_matrix(context):
    """
    Markov Transition Matrix
    for volatility regimes.
    """

    vr = context.get_result("volatility_regime")

    if vr is None:
        return None

    regimes = vr["regime_series"]

    states = ["LOW", "MEDIUM", "HIGH"]
    counts = {s: {t: 0 for t in states} for s in states}

    for i in range(len(regimes) - 1):
        counts[regimes[i]][regimes[i+1]] += 1

    matrix = {}

    for s in states:
        total = sum(counts[s].values())
        matrix[s] = (
            {t: counts[s][t] / total for t in states}
            if total > 0 else {t: 0.0 for t in states}
        )

    return matrix


registry.register(
    "regime_transition_matrix",
    regime_transition_matrix,
    category="regimes",
    dependencies=["volatility_regime"]
)