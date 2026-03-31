import numpy as np
from core.registry import registry


def execution_impact_model(context):
    """
    Institutional Deployability Impact Model

    Converts capital allocation into
    ADV-based participation impact path.

    Uses:
        - Square-root market impact law
        - ADV participation scaling
        - EWMA volatility coupling
        - Spread regime temporary impact
    """

    aligned = context.get_cache("aligned_strategy_returns")
    weights = context.get_result("capital_engine")
    spreads = context.get_cache("regime_spread_matrix")

    if aligned is None or weights is None or spreads is None:
        return None

    keys, R = aligned
    R = np.asarray(R, dtype=np.float64)

    N, T = R.shape

    if spreads.shape != (N, T):
        return None

    w = np.array([weights[k] for k in keys], dtype=np.float64)

    if not np.isfinite(w).all() or np.sum(w) == 0:
        return None

    w = w / np.sum(w)

    total_capital = context.data.get("total_capital", 1_000_000)

    # ---------------------------------------------------
    # ADV Proxy (market capacity)
    # ---------------------------------------------------
    adv_proxy = context.data.get("adv_proxy", 50_000_000)

    # participation cap (institutional execution range)
    max_participation = context.data.get("max_participation", 0.03)

    # square-root exponent
    alpha = context.data.get("impact_exponent", 0.5)

    # permanent impact coefficient
    gamma = context.data.get("perm_impact_coeff", 0.5)

    # ---------------------------------------------------
    # Volatility EWMA
    # ---------------------------------------------------
    lam = context.data.get("impact_ewma_lambda", 0.94)

    vol = np.zeros((N, T))
    vol[:, 0] = np.var(R, axis=1)

    for t in range(1, T):
        vol[:, t] = (
            lam * vol[:, t-1]
            + (1 - lam) * (R[:, t-1] ** 2)
        )

    vol = np.sqrt(vol)

    # ---------------------------------------------------
    # Participation Model
    # ---------------------------------------------------
    impact_matrix = np.zeros((N, T))

    for i in range(N):

        alloc_cap = w[i] * total_capital

        # ADV participation
        participation = alloc_cap / adv_proxy
        participation = min(max_participation, participation)

        nonlinear = participation ** alpha

        temp_impact = spreads[i] * nonlinear
        perm_impact = vol[i] * nonlinear * gamma

        impact_matrix[i] = temp_impact + perm_impact

    # ---------------------------------------------------
    # Adjusted Return Path
    # ---------------------------------------------------
    adjusted = R - impact_matrix

    port_adj = np.sum(adjusted.T * w, axis=1)

    if not np.isfinite(port_adj).all():
        return None

    context.set_cache("impact_adjusted_returns", port_adj)

    return port_adj


registry.register(
    "execution_impact_model",
    execution_impact_model,
    category="stress",
    dependencies=[
        "portfolio_preprocessor",
        "capital_engine",
        "spread_regime_generator"
    ]
)