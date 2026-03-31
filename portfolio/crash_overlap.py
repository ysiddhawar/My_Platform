import numpy as np
from core.registry import registry


def crash_overlap(context):

    R = context.get_cache("strategy_returns")

    if R is None:
        return None

    R = np.asarray(R, dtype=np.float64)

    if R.ndim != 2 or R.shape[1] < 2:
        return None

    T, N = R.shape

    if T < 30:
        return None

    equity = np.cumprod(1 + R, axis=0)
    peaks = np.maximum.accumulate(equity, axis=0)
    dd = (equity - peaks) / peaks

    crash_masks = np.zeros_like(dd, dtype=bool)

    for i in range(N):
        thresh = np.percentile(dd[:, i], 5)
        crash_masks[:, i] = dd[:, i] <= thresh

    overlap = np.zeros((N, N), dtype=np.float64)

    for i in range(N):
        for j in range(N):
            joint = np.logical_and(
                crash_masks[:, i],
                crash_masks[:, j]
            )
            overlap[i, j] = np.mean(joint)

    return overlap.tolist()


registry.register(
    "crash_overlap",
    crash_overlap,
    category="portfolio",
    dependencies=["portfolio_preprocessor"]
)