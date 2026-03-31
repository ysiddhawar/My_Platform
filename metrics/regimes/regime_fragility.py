import numpy as np
from core.registry import registry


def regime_fragility(context):
    """
    Regime Fragility Score

    Measures dispersion of performance
    across volatility regimes.

    Higher score → unstable regime behavior
    """

    breakdown = context.get_result("regime_breakdown")

    if breakdown is None or len(breakdown) < 2:
        return None

    sharpes = []
    drawdowns = []

    for regime_data in breakdown.values():

        if regime_data is None:
            continue

        s = regime_data.get("sharpe")
        d = regime_data.get("max_drawdown")

        if s is not None:
            sharpes.append(s)

        if d is not None:
            drawdowns.append(abs(d))

    if len(sharpes) < 2 or len(drawdowns) < 2:
        return None

    sharpe_dispersion = np.std(sharpes, ddof=1)
    dd_dispersion = np.std(drawdowns, ddof=1)

    fragility_score = sharpe_dispersion + dd_dispersion

    return float(fragility_score)


registry.register(
    "regime_fragility",
    regime_fragility,
    category="regimes",
    dependencies=[
        "regime_breakdown"
    ]
)