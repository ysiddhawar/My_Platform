import numpy as np
from core.registry import registry


def portfolio_fragility_index(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    T, N = R.shape
    if N < 2 or T < 50:
        return None

    weights = context.get_result("risk_parity")

    if weights is None:
        w = np.ones(N) / N
    else:
        w = np.array([weights[n] for n in names], dtype=np.float64)

    if np.sum(w) <= 1e-12:
        return None

    w /= np.sum(w)

    # -----------------------------------------
    # Risk concentration
    # -----------------------------------------
    vol = np.std(R, axis=0, ddof=1)
    rc = w * vol
    risk_conc = np.std(rc)

    # -----------------------------------------
    # Correlation concentration
    # -----------------------------------------
    corr = np.corrcoef(R, rowvar=False)
    upper = corr[np.triu_indices_from(corr, k=1)]
    avg_corr = np.mean(np.abs(upper))

    # -----------------------------------------
    # Systemic Fragility (DAG-fed)
    # -----------------------------------------
    systemic = context.get_result("systemic_fragility")
    if systemic is None:
        return None

    frag = (
        risk_conc
        + avg_corr
        + systemic["systemic_fragility_score"]
    )

    return float(frag)


registry.register(
    "portfolio_fragility_index",
    portfolio_fragility_index,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "systemic_fragility",
        "risk_parity"
    ]
)