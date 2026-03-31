# stress/spread_regime_generator.py

import numpy as np
from core.registry import registry


def spread_regime_generator(context):
    """
    Institutional Liquidity Regime Generator

    Simulates persistent microstructure spread regimes:

        - Calm liquidity state
        - Transitional liquidity state
        - Liquidity drought state

    Uses:
        - Volatility-coupled Markov regime switching
        - Mean-reverting spread state dynamics
        - Endogenous persistence

    Caches:
        regime_spread_matrix  -> (N x T)

    Requires:
        aligned_strategy_returns
    """

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    N, T = R.shape
    if T < 50:
        return None

    # -----------------------------------------
    # EWMA Volatility Driver
    # -----------------------------------------
    lam = context.data.get("spread_ewma_lambda", 0.94)

    vol = np.zeros((N, T))
    vol[:, 0] = np.var(R, axis=1)

    for t in range(1, T):
        vol[:, t] = (
            lam * vol[:, t-1]
            + (1 - lam) * (R[:, t-1] ** 2)
        )

    vol = np.sqrt(vol)

    # -----------------------------------------
    # Markov Liquidity Regimes
    # 0 = calm
    # 1 = transition
    # 2 = drought
    # -----------------------------------------
    base_spread = context.data.get("base_spread", 0.0001)

    regime_spreads = np.zeros((N, T))
    regimes = np.zeros((N, T), dtype=int)

    for i in range(N):

        regimes[i, 0] = 0
        regime_spreads[i, 0] = base_spread

        for t in range(1, T):

            v = vol[i, t]

            # volatility-driven transition probabilities
            p_up = min(0.3, v * 50)
            p_down = max(0.05, 0.2 - v * 10)

            state = regimes[i, t-1]

            if state == 0:
                if np.random.rand() < p_up:
                    state = 1

            elif state == 1:
                r = np.random.rand()
                if r < p_up:
                    state = 2
                elif r < p_up + p_down:
                    state = 0

            elif state == 2:
                if np.random.rand() < p_down:
                    state = 1

            regimes[i, t] = state

            # Mean-reverting spread process
            if state == 0:
                target = base_spread
            elif state == 1:
                target = base_spread * 1.8
            else:
                target = base_spread * 4.0

            prev = regime_spreads[i, t-1]

            regime_spreads[i, t] = (
                0.85 * prev
                + 0.15 * target
                + base_spread * 0.05 * np.random.randn()
            )

    regime_spreads = np.abs(regime_spreads)

    context.set_cache("regime_spread_matrix", regime_spreads)

    return regime_spreads


registry.register(
    "spread_regime_generator",
    spread_regime_generator,
    category="stress",
    dependencies=[
        "portfolio_preprocessor"
    ]
)