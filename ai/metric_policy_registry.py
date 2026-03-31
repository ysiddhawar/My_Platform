from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any


# ============================================================
# Metric Policy Definition
# ============================================================

@dataclass(frozen=True)
class MetricPolicy:
    """
    Defines governance and interpretation rules for a metric.

    direction:
        - "higher_better"
        - "lower_better"
        - "range"

    adaptive_mode:
        - "percentile" (recommended)
        - "zscore"
        - None (fallback)

    tier_thresholds:
        Dict of:
        {
            "survival": value,
            "consistency": value,
            "profitable": value
        }
    """

    category: str
    direction: str
    adaptive_mode: Optional[str]
    tier_thresholds: Dict[str, Any]


# ============================================================
# Registry
# ============================================================

class MetricPolicyRegistry:
    """
    Central Governance Layer for ALL metrics in My_Platform.

    Responsibilities:
    - Store policies for every metric
    - Provide tier-aware thresholds
    - Provide direction awareness
    - Enable adaptive interpretation
    """

    def __init__(self):
        self._policies: Dict[str, MetricPolicy] = {}
        self._register_all_metrics()

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def get_policy(self, metric_name: str) -> Optional[MetricPolicy]:
        return self._policies.get(metric_name)

    def list_all_metrics(self):
        return list(self._policies.keys())

    # --------------------------------------------------------
    # Adaptive Threshold Logic
    # --------------------------------------------------------

    def evaluate(
        self,
        metric_name: str,
        value: float,
        tier: str,
        percentile: Optional[float] = None,
        zscore: Optional[float] = None,
    ) -> Optional[str]:
        """
        Returns:
            "pass", "fail", or None
        """

        policy = self.get_policy(metric_name)
        if not policy:
            return None

        threshold = policy.tier_thresholds.get(tier)
        if threshold is None:
            return None

        # Adaptive percentile mode
        if policy.adaptive_mode == "percentile" and percentile is not None:
            if policy.direction == "higher_better":
                return "pass" if percentile >= threshold else "fail"
            if policy.direction == "lower_better":
                return "pass" if percentile <= threshold else "fail"

        # Adaptive zscore mode
        if policy.adaptive_mode == "zscore" and zscore is not None:
            if policy.direction == "higher_better":
                return "pass" if zscore >= threshold else "fail"
            if policy.direction == "lower_better":
                return "pass" if zscore <= threshold else "fail"

        # Fallback static comparison
        if policy.direction == "higher_better":
            return "pass" if value >= threshold else "fail"

        if policy.direction == "lower_better":
            return "pass" if value <= threshold else "fail"

        return None

    # --------------------------------------------------------
    # Full Metric Registration
    # --------------------------------------------------------

    def _register_all_metrics(self):

        # ----------------------------
        # JOURNAL
        # ----------------------------

        self._add("win_rate", "journal", "higher_better", "percentile")
        self._add("loss_rate", "journal", "lower_better", "percentile")
        self._add("average_win", "journal", "higher_better", "percentile")
        self._add("average_loss", "journal", "lower_better", "percentile")
        self._add("payoff_ratio", "journal", "higher_better", "percentile")
        self._add("profit_factor", "journal", "higher_better", "percentile")
        self._add("expectancy", "journal", "higher_better", "percentile")
        self._add("cumulative_net_pnl", "journal", "higher_better", "percentile")

        # ----------------------------
        # PERFORMANCE
        # ----------------------------

        for metric in [
            "sharpe",
            "sortino",
            "calmar",
            "cagr",
            "rolling_sharpe",
            "net_sharpe",
            "net_cagr",
        ]:
            self._add(metric, "performance", "higher_better", "percentile")

        # ----------------------------
        # RISK
        # ----------------------------

        for metric in [
            "volatility",
            "rolling_volatility",
            "adaptive_rolling_volatility",
            "max_drawdown",
            "rolling_drawdown",
            "drawdown_duration",
            "ulcer_index",
            "downside_deviation",
            "var",
            "cvar",
        ]:
            self._add(metric, "risk", "lower_better", "percentile")

        # ----------------------------
        # DISTRIBUTIONS
        # ----------------------------

        for metric in [
            "normality_test",
            "skewness",
            "kurtosis",
            "fat_tail_index",
            "tail_ratio",
            "student_t_fit",
            "pareto_fit",
            "power_law_exponent",
            "lognormal_test",
            "autocorrelation",
            "pareto_tail_estimator",
            "power_law_fit",
        ]:
            self._add(metric, "distributions", "range", "percentile")

        # ----------------------------
        # REGIMES
        # ----------------------------

        for metric in [
            "volatility_regime",
            "regime_labeling",
            "regime_sharpe",
            "regime_drawdown",
            "regime_transition_matrix",
            "regime_switching",
            "volatility_clustering",
            "garch_volatility",
            "regime_breakdown",
            "regime_fragility",
        ]:
            self._add(metric, "regimes", "range", "percentile")

        # ----------------------------
        # ROBUSTNESS
        # ----------------------------

        for metric in [
            "walk_forward",
            "bootstrap",
            "block_bootstrap",
            "parameter_sensitivity",
            "noise_stability",
            "regime_stability",
            "monte_carlo_stability",
            "stability_score",
        ]:
            self._add(metric, "robustness", "higher_better", "percentile")

        # ----------------------------
        # PORTFOLIO
        # ----------------------------

        for metric in [
            "correlation",
            "covariance_matrix",
            "portfolio_variance",
            "risk_contribution",
            "risk_parity",
            "target_volatility",
            "drawdown_correlation",
            "crash_overlap",
            "systemic_fragility",
            "portfolio_fragility_index",
            "portfolio_preprocessor",
            "diversification_ratio",
            "effective_number_of_bets",
            "hierarchical_risk_parity",
            "dynamic_cluster_risk_budgeting",
            "drawdown_aware_capital_allocator",
        ]:
            self._add(metric, "portfolio", "range", "percentile")

        # ----------------------------
        # CAPITAL
        # ----------------------------

        for metric in [
            "risk_budgeting",
            "kelly",
            "portfolio_position_sizer",
            "position_sizer",
            "capital_engine",
        ]:
            self._add(metric, "capital", "range", "percentile")

        # ----------------------------
        # RISK CONTROL
        # ----------------------------

        for metric in [
            "kill_switch",
            "throttle",
            "capital_throttle_engine",
        ]:
            self._add(metric, "risk_control", "range", "percentile")

        # ----------------------------
        # STRESS
        # ----------------------------

        for metric in [
            "stress_engine",
            "volatility_spike",
            "liquidity_shock",
            "correlation_spike",
            "crash_simulation",
            "stress_scenarios",
            "regime_path_generator",
            "spread_regime_generator",
            "execution_impact_model",
        ]:
            self._add(metric, "stress", "range", "percentile")

        # ----------------------------
        # SURVIVAL
        # ----------------------------

        for metric in [
            "fragility_score",
            "deployable_leverage",
            "kill_switch_threshold",
            "capital_throttle_policy",
            "drawdown_percentile",
            "capital_decay",
            "risk_of_ruin",
            "ruin_probability_mc",
            "survival_score",
            "survival_engine",
        ]:
            self._add(metric, "survival", "range", "percentile")

    # --------------------------------------------------------
    # Internal Helper
    # --------------------------------------------------------

    def _add(
        self,
        name: str,
        category: str,
        direction: str,
        adaptive_mode: str,
    ):
        self._policies[name] = MetricPolicy(
            category=category,
            direction=direction,
            adaptive_mode=adaptive_mode,
            tier_thresholds={
                "survival": 30,
                "consistency": 50,
                "profitable": 70,
            },
        )