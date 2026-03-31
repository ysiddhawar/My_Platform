import numpy as np
from core.registry import registry


def calmar(context):

    cagr_val = context.get_result("cagr")
    mdd_val = context.get_result("max_drawdown")

    if cagr_val is None or mdd_val is None:
        return None

    if mdd_val == 0:
        return float("inf")

    return float(cagr_val / abs(mdd_val))


registry.register(
    "calmar",
    calmar,
    category="performance",
    dependencies=[
        "cagr",
        "max_drawdown"
    ]
)