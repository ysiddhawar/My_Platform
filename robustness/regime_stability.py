import numpy as np
from core.registry import registry


def regime_stability(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size

    if n < 60:
        return None

    vol = np.abs(returns)

    q_low, q_high = np.quantile(vol,[0.33,0.66])

    low  = returns[vol<=q_low]
    mid  = returns[(vol>q_low)&(vol<=q_high)]
    high = returns[vol>q_high]

    def sharpe(x):

        if x.size < 20:
            return None

        mu = np.mean(x)
        sd = np.std(x,ddof=1)

        return mu/sd if sd>0 else None

    s_low  = sharpe(low)
    s_mid  = sharpe(mid)
    s_high = sharpe(high)

    vals = np.asarray(
        [v for v in [s_low,s_mid,s_high] if v is not None]
    )

    if vals.size < 2:
        return None

    mean = np.mean(vals)
    std  = np.std(vals)

    return {
        "low_regime": float(s_low) if s_low else None,
        "mid_regime": float(s_mid) if s_mid else None,
        "high_regime": float(s_high) if s_high else None,
        "regime_volatility": float(std),
        "regime_fragility": float(std/abs(mean)) if mean!=0 else None
    }


registry.register(
    "regime_stability",
    regime_stability,
    category="robustness",
    dependencies=["adjusted_pnl"]
)