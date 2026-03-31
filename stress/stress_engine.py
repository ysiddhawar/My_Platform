import numpy as np
from core.registry import registry


def stress_engine(context):
    """
    Institutional Multi-Layer Stress Aggregator

    Aggregates:
        - Base portfolio DD
        - Correlation regime collapse
        - Crash simulation
        - Scenario generator
        - Liquidity shock friction
        - Regime-path stress
        - Execution impact adjusted DD

    Produces:
        Worst deployable capital drawdown
    """

    aligned = context.get_cache("aligned_strategy_returns")
    weights = context.get_result("capital_engine")
    regime_paths = context.get_result("regime_path_generator")
    crash = context.get_result("crash_simulation")
    scen = context.get_result("stress_scenarios")
    liq = context.get_result("liquidity_shock")
    impact_path = context.get_result("execution_impact_model")

    if aligned is None or weights is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    if R.shape[1] < 50:
        return None

    w = np.array([weights[k] for k in keys], dtype=np.float64)

    if not np.isfinite(w).all():
        return None
    if np.sum(w) == 0:
        return None

    w = w / np.sum(w)

    def compute_dd(x):
        eq = np.cumprod(1 + x)
        pk = np.maximum.accumulate(eq)
        return float(np.min((eq - pk) / pk))

    # ---------------------------------------------------
    # Base Portfolio
    # ---------------------------------------------------
    base_port = np.sum(R.T * w, axis=1)
    base_dd = compute_dd(base_port)

    # ---------------------------------------------------
    # Correlation Regime Stress
    # ---------------------------------------------------
    cov = np.cov(R)
    std = np.sqrt(np.diag(cov))

    corr_spike = np.ones_like(cov) * 0.8
    np.fill_diagonal(corr_spike, 1.0)

    stressed_cov = np.outer(std, std) * corr_spike

    try:
        chol = np.linalg.cholesky(stressed_cov)
        shocked = chol @ np.random.normal(size=(len(keys), R.shape[1]))
        corr_port = np.sum(shocked.T * w, axis=1)
        corr_dd = compute_dd(corr_port)
    except np.linalg.LinAlgError:
        corr_dd = 0.0

    # ---------------------------------------------------
    # Crash Simulation Aggregation
    # ---------------------------------------------------
    crash_dd = 0.0
    if crash is not None:
        vals = [
            crash[k]["worst_case_drawdown"]
            for k in crash.keys()
            if "worst_case_drawdown" in crash[k]
        ]
        if vals:
            crash_dd = float(min(vals))

    # ---------------------------------------------------
    # Scenario Generator
    # ---------------------------------------------------
    scen_dd = 0.0
    if scen is not None:
        vals = [
            scen[k]["worst_case"]
            for k in scen.keys()
            if "worst_case" in scen[k]
        ]
        if vals:
            scen_dd = float(min(vals))

    # ---------------------------------------------------
    # Liquidity Shock Aggregation
    # ---------------------------------------------------
    liq_dd = 0.0

    spread_matrix = context.data.get("spread_matrix")

    if spread_matrix is not None:

        S = np.asarray(spread_matrix, dtype=np.float64)

        if S.shape == R.shape:

            # participation rate (how much book you take)
            participation = context.data.get(
                "stress_participation_rate",
                0.05
            )

            # turnover proxy aligned to T using prepended initial state
            turnover = np.mean(
                np.abs(np.diff(R, axis=1, prepend=R[:, :1])),
                axis=0
            )
            turnover = np.clip(turnover, 0, 1)

            # square-root impact model
            liq_lambda = context.data.get(
                "stress_liquidity_lambda",
                2.5
            )

            spread_weighted = np.sum(S.T * w, axis=1)

            impact = (
                liq_lambda *
                np.sqrt(max(float(participation), 0.0)) *
                spread_weighted *
                turnover
            )
            impact = np.nan_to_num(impact, nan=0.0, posinf=0.0, neginf=0.0)

            liq_port = base_port - impact

            if np.isfinite(liq_port).all():
                liq_dd = compute_dd(liq_port)

    # ---------------------------------------------------
    # Regime Simulation
    # ---------------------------------------------------
    regime_dd = 0.0
    if regime_paths is not None:
        regime_port = np.sum(regime_paths.T * w, axis=1)
        regime_dd = compute_dd(regime_port)

    # ---------------------------------------------------
    # Execution Impact Stress
    # ---------------------------------------------------
    impact_dd = 0.0
    if impact_path is not None:
        impact_dd = compute_dd(np.asarray(impact_path))

    # ---------------------------------------------------
    # Worst Deployable DD
    # ---------------------------------------------------
    worst_dd = min([
        base_dd,
        corr_dd,
        crash_dd,
        scen_dd,
        liq_dd,
        regime_dd,
        impact_dd
    ])

    return {
        "base_drawdown": float(base_dd),
        "corr_regime_dd": float(corr_dd),
        "crash_dd": float(crash_dd),
        "liquidity_dd": float(liq_dd),
        "scenario_dd": float(scen_dd),
        "regime_dd": float(regime_dd),
        "execution_impact_dd": float(impact_dd),
        "worst_case_dd": float(worst_dd)
    }


registry.register(
    "stress_engine",
    stress_engine,
    category="stress",
    dependencies=[
        "portfolio_preprocessor",
        "capital_engine",
        "volatility_spike",
        "correlation_spike",
        "crash_simulation",
        "liquidity_shock",
        "stress_scenarios",
        "regime_path_generator",
        "spread_regime_generator",
        "execution_impact_model"
    ]
)