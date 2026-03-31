import numpy as np
from core.registry import registry


def stability_score(context):

    noise  = context.get_result("noise_stability")
    regime = context.get_result("regime_stability")
    block  = context.get_result("block_bootstrap")
    mc     = context.get_result("monte_carlo_stability")

    comps = []

    if noise:
        s = noise.get("stability_ratio")
        if s is not None:
            comps.append(s)

    if regime:
        f = regime.get("regime_fragility")
        if f is not None:
            comps.append(max(0,1-f))

    if block:
        w = block.get("worst_5pct")
        if w is not None:
            comps.append(max(0,1-abs(w)))

    if mc:
        crash = mc.get("crash_probability")
        if crash is not None:
            comps.append(max(0,1-crash))

    if len(comps)<2:
        return None

    composite = float(np.mean(comps))

    return {
        "stability_score": composite,
        "stability_grade":
            "ROBUST"   if composite>0.75 else
            "MODERATE" if composite>0.5  else
            "FRAGILE"
    }


registry.register(
    "stability_score",
    stability_score,
    category="robustness",
    dependencies=[
        "noise_stability",
        "regime_stability",
        "block_bootstrap",
        "monte_carlo_stability"
    ]
)