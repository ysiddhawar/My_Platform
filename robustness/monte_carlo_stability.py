import numpy as np
from scipy import stats
from core.registry import registry


def monte_carlo_stability(context):

    returns = context.get_cache("net_returns")

    if returns is None:
        return None

    returns = np.asarray(returns,dtype=np.float64)
    n = returns.size

    if n < 30:
        return None

    rng = np.random.default_rng(42)

    n_sims = max(500,int(np.sqrt(n)*30))

    kurt = stats.kurtosis(returns,fisher=True)
    dist = "student-t" if kurt>1 else "normal"

    sims = np.empty(n_sims)

    if dist=="normal":

        mu = np.mean(returns)
        sd = np.std(returns,ddof=1)

        for i in range(n_sims):
            sim = rng.normal(mu,sd,n)
            sims[i] = np.prod(1+sim)-1

    else:

        df,loc,scale = stats.t.fit(returns)

        for i in range(n_sims):
            sim = stats.t.rvs(
                df,
                loc=loc,
                scale=scale,
                size=n,
                random_state=rng
            )
            sims[i] = np.prod(1+sim)-1

    return {
        "median": float(np.median(sims)),
        "worst_5pct": float(np.percentile(sims,5)),
        "worst_1pct": float(np.percentile(sims,1)),
        "crash_probability": float(np.mean(sims<-0.3))
    }


registry.register(
    "monte_carlo_stability",
    monte_carlo_stability,
    category="robustness",
    dependencies=["adjusted_pnl"]
)