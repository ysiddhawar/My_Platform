import numpy as np
from core.registry import registry


def kelly(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    frac = context.data.get("fractional_kelly", 0.5)
    max_lev = context.data.get("max_leverage", 3.0)

    frag = context.get_result("systemic_fragility")
    frag_scale = 1.0

    if frag is not None:
        frag_scale = max(0.1, 1 - frag["systemic_fragility_score"])

    kelly_vec = []

    for i in range(R.shape[0]):

        r = R[i]
        wins = r[r > 0]
        losses = r[r < 0]

        if len(wins) < 5 or len(losses) < 5:
            kelly_vec.append(0.0)
            continue

        p = len(wins) / len(r)
        q = 1 - p

        b = np.mean(wins) / abs(np.mean(losses))

        if b == 0:
            kelly_vec.append(0.0)
            continue

        k = (p - q / b)

        equity = np.cumprod(1 + r)
        peak = np.maximum.accumulate(equity)
        dd = (equity - peak) / peak
        max_dd = abs(np.min(dd))

        k *= max(0.0, 1 - max_dd)
        k *= frac
        k *= frag_scale

        kelly_vec.append(min(max(k, 0.0), max_lev))

    return dict(zip(keys, kelly_vec))


registry.register(
    "kelly",
    kelly,
    category="capital",
    dependencies=[
        "portfolio_preprocessor",
        "systemic_fragility"
    ]
)