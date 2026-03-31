import numpy as np
from scipy import stats
from core.registry import registry


def student_t_fit(context):
    """
    Institutional Student-t Fit Engine

    - Uses cost-adjusted net returns
    - Cached distribution stream
    - Robust to NaN
    - Returns df (tail thickness indicator)
    """

    returns = context.get_cache("dist_clean_returns")

    if returns is None or returns.size < 50:
        return None

    try:
        df, loc, scale = stats.t.fit(returns)

        if df <= 2:
            tail_heaviness = np.inf
        else:
            tail_heaviness = 1.0 / df

        return {
            "df": float(df),
            "loc": float(loc),
            "scale": float(scale),
            "implied_tail_heaviness": float(tail_heaviness)
        }

    except Exception:
        return None


registry.register(
    "student_t_fit",
    student_t_fit,
    category="distributions",
    dependencies=["normality_test"]
)