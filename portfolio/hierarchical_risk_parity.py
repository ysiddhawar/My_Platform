import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
from core.registry import registry


def hierarchical_risk_parity(context):

    R = context.get_cache("strategy_returns")
    names = context.get_cache("strategy_names")

    if R is None or names is None:
        return None

    T, N = R.shape
    if N < 2 or T < 50:
        return None

    # -----------------------------------------
    # Correlation → Distance Matrix
    # -----------------------------------------
    corr = np.corrcoef(R, rowvar=False)

    dist = np.sqrt(0.5 * (1 - corr))
    dist = np.nan_to_num(dist)

    try:
        link = linkage(squareform(dist), method="single")
    except Exception:
        return None

    # -----------------------------------------
    # Quasi Diagonalization
    # -----------------------------------------
    sort_ix = _get_quasi_diag(link)
    R = R[:, sort_ix]
    corr = corr[np.ix_(sort_ix, sort_ix)]

    # -----------------------------------------
    # Recursive Bisection
    # -----------------------------------------
    weights = _recursive_bisection(corr)

    final_w = np.zeros(N)
    final_w[sort_ix] = weights

    return dict(zip(names, final_w.tolist()))


# ------------------------------------------------
# INTERNAL HELPERS
# ------------------------------------------------

def _get_quasi_diag(link):

    link = link.astype(int)
    sort_ix = [link[-1, 0], link[-1, 1]]

    num_items = link[-1, 3]

    while max(sort_ix) >= num_items:
        sort_ix_new = []

        for i in sort_ix:
            if i >= num_items:
                i1 = link[i - num_items, 0]
                i2 = link[i - num_items, 1]
                sort_ix_new += [i1, i2]
            else:
                sort_ix_new.append(i)

        sort_ix = sort_ix_new

    return sort_ix


def _get_cluster_var(corr):

    inv_diag = 1 / np.diag(corr)
    weights = inv_diag / np.sum(inv_diag)

    var = weights.T @ corr @ weights
    return var


def _recursive_bisection(corr):

    w = np.ones(len(corr))
    clusters = [list(range(len(corr)))]

    while len(clusters) > 0:

        clusters = [
            cluster[j:k]
            for cluster in clusters
            for j, k in (
                (0, len(cluster) // 2),
                (len(cluster) // 2, len(cluster))
            )
            if len(cluster) > 1
        ]

        for i in range(0, len(clusters), 2):

            c1 = clusters[i]
            c2 = clusters[i + 1]

            corr1 = corr[np.ix_(c1, c1)]
            corr2 = corr[np.ix_(c2, c2)]

            var1 = _get_cluster_var(corr1)
            var2 = _get_cluster_var(corr2)

            alpha = 1 - var1 / (var1 + var2)

            w[c1] *= alpha
            w[c2] *= 1 - alpha

    return w


registry.register(
    "hierarchical_risk_parity",
    hierarchical_risk_parity,
    category="portfolio",
    dependencies=[
        "portfolio_preprocessor",
        "correlation"
    ]
)