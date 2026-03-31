import numpy as np
from core.registry import registry


def portfolio_preprocessor(context):
    """
    Institutional Portfolio Data Normalizer

    Converts:
        context.data["strategies"]
            ↓
        strategy_returns : (T × N) matrix

    Caches:
        strategy_returns
        strategy_names

    Guarantees:
    - Deterministic ordering
    - Shape safety
    - NaN filtering
    - Equal-length alignment
    """

    strategies = context.data.get("strategies")

    if not strategies or not isinstance(strategies, dict):
        return None

    names = []
    aligned = []

    min_len = None

    for name, series in strategies.items():
        if isinstance(series, dict):
            raise ValueError(
                "Invalid strategies payload: each strategy value must be "
                "a 1D returns array, not a dict. "
                f"Got dict for strategy '{name}'."
            )

        arr = np.asarray(series, dtype=np.float64)

        if arr.ndim != 1 or arr.size == 0:
            continue

        arr = arr[np.isfinite(arr)]

        if arr.size == 0:
            continue

        if min_len is None:
            min_len = arr.size
        else:
            min_len = min(min_len, arr.size)

        names.append(name)
        aligned.append(arr)

    if not aligned or min_len < 2:
        return None

    trimmed = [a[-min_len:] for a in aligned]

    matrix = np.column_stack(trimmed)

    context.set_cache("strategy_returns", matrix)
    context.set_cache("strategy_names", names)
    # Backward-compatible alias expected by legacy capital modules:
    # (names, returns_matrix as N x T)
    context.set_cache("aligned_strategy_returns", (names, matrix.T))

    return matrix


registry.register(
    "portfolio_preprocessor",
    portfolio_preprocessor,
    category="portfolio"
)