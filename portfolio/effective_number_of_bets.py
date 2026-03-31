import numpy as np
from core.registry import registry


def effective_number_of_bets(context):

    R = context.get_cache("strategy_returns")
    if R is None:
        return None

    T, N = R.shape
    if N < 2 or T < 30:
        return None

    corr = np.corrcoef(R, rowvar=False)

    if not np.all(np.isfinite(corr)):
        return None

    try:
        eigvals = np.linalg.eigvalsh(corr)
    except Exception:
        return None

    eigvals = eigvals[eigvals > 1e-12]
    if len(eigvals) == 0:
        return None

    numerator = np.sum(eigvals) ** 2
    denominator = np.sum(eigvals ** 2)

    if denominator <= 1e-12:
        return None

    return float(numerator / denominator)


registry.register(
    "effective_number_of_bets",
    effective_number_of_bets,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)