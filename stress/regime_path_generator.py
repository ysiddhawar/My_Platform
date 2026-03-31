import numpy as np
from core.registry import registry


def regime_path_generator(context):

    aligned = context.get_cache("aligned_strategy_returns")
    if aligned is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    n_strat, T = R.shape
    if T < 100:
        return None

    # -----------------------------
    # Adaptive Parameters
    # -----------------------------
    base_low = context.data.get("regime_low_vol", 0.008)
    base_high = context.data.get("regime_high_vol", 0.04)

    regime_switch_base = context.data.get("regime_switch_prob", 0.015)
    jump_prob = context.data.get("jump_probability", 0.004)
    jump_scale = context.data.get("jump_scale", 0.12)

    persistence = context.data.get("trend_persistence", 0.18)
    vol_memory = context.data.get("volatility_memory", 0.92)
    leverage_beta = context.data.get("leverage_effect", 0.25)

    simulated = np.zeros((n_strat, T))
    conditional_vol = np.ones(n_strat) * base_low
    regime_state = 0

    for t in range(1, T):

        # -----------------------------
        # Regime switching driven by vol
        # -----------------------------
        vol_pressure = np.mean(conditional_vol) / base_high
        p_switch = min(regime_switch_base * (1 + vol_pressure), 0.5)

        if np.random.rand() < p_switch:
            regime_state = 1 - regime_state

        target_vol = base_low if regime_state == 0 else base_high

        # -----------------------------
        # GARCH-like volatility feedback
        # -----------------------------
        conditional_vol = (
            vol_memory * conditional_vol
            + (1 - vol_memory) * np.abs(simulated[:, t - 1])
        )

        conditional_vol = np.clip(conditional_vol, 1e-5, target_vol)

        # -----------------------------
        # Fat-tail innovation
        # -----------------------------
        shock = np.random.standard_t(df=4, size=n_strat)

        # -----------------------------
        # Leverage effect
        # -----------------------------
        downside = simulated[:, t - 1] < 0
        conditional_vol *= (1 + leverage_beta * downside)

        noise = shock * conditional_vol

        # -----------------------------
        # Trend persistence
        # -----------------------------
        trend = persistence * simulated[:, t - 1]

        # -----------------------------
        # Jump diffusion
        # -----------------------------
        jump_mask = np.random.rand(n_strat) < jump_prob
        jumps = jump_mask * np.random.normal(0, jump_scale, n_strat)

        simulated[:, t] = noise + trend + jumps

    context.set_cache("regime_simulated_returns", simulated)

    return simulated


registry.register(
    "regime_path_generator",
    regime_path_generator,
    category="stress",
    dependencies=["portfolio_preprocessor"]
)