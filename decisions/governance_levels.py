from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


class GovernanceError(Exception):
    pass


@dataclass(frozen=True)
class GovernanceTier:
    name: str
    min_score: float
    description: str


class GovernanceLevels:
    """
    Institutional Governance Classification Engine

    Responsibilities:
    - Evaluate ALL platform outputs (metrics + engines)
    - Compute structural composite score
    - Classify trader tier
    - NEVER restrict execution
    - Deterministic, replay-safe, versioned
    """

    VERSION = 3

    TIERS = [
        GovernanceTier("dying", 0.0, "Severe structural fragility detected."),
        GovernanceTier("survival", 40.0, "Basic capital preservation achieved."),
        GovernanceTier("consistency", 65.0, "Stable and repeatable structure."),
        GovernanceTier("profitable", 80.0, "Institutional-grade robustness."),
    ]

    # =========================================================
    # PUBLIC ENTRY
    # =========================================================

    @classmethod
    def classify(
        cls,
        structured_data: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:

        """
        structured_data must include:

        {
            "metrics": {...},          # metrics/*
            "robustness": {...},       # robustness/*
            "portfolio": {...},        # portfolio/*
            "capital": {...},          # capital/*
            "risk_control": {...},     # risk_control/*
            "stress": {...},           # stress/*
            "survival": {...},         # survival/*
        }
        """

        if not isinstance(structured_data, dict):
            raise GovernanceError("structured_data must be dict")

        metrics = structured_data.get("metrics", {})
        robustness = structured_data.get("robustness", {})
        portfolio = structured_data.get("portfolio", {})
        capital = structured_data.get("capital", {})
        risk_control = structured_data.get("risk_control", {})
        stress = structured_data.get("stress", {})
        survival = structured_data.get("survival", {})

        category_scores = {
            "metrics": cls._score_metrics(metrics),
            "robustness": cls._score_robustness(robustness),
            "portfolio": cls._score_portfolio(portfolio),
            "capital": cls._score_capital(capital),
            "risk_control": cls._score_risk_control(risk_control),
            "stress": cls._score_stress(stress),
            "survival": cls._score_survival(survival),
        }

        total_score = cls._aggregate(category_scores)
        tier = cls._resolve_tier(total_score)

        return {
            "tier": tier.name,
            "score": total_score,
            "category_scores": category_scores,
            "description": tier.description,
            "version": cls.VERSION,
        }

    # =========================================================
    # METRICS SCORING (metrics/*)
    # =========================================================

    @staticmethod
    def _score_metrics(metrics: Dict[str, Any]) -> float:
        score = 0.0

        # Journal
        journal = metrics.get("journal", {})
        score += min(journal.get("win_rate", 0) * 100, 15)
        score += min(journal.get("profit_factor", 0) * 10, 15)
        score += min(journal.get("expectancy", 0) * 100, 10)

        # Performance
        performance = metrics.get("performance", {})
        score += min(performance.get("sharpe", 0) * 8, 15)
        score += min(performance.get("sortino", 0) * 6, 10)
        score += min(performance.get("calmar", 0) * 5, 10)
        score += min(performance.get("cagr", 0) * 2, 10)
        score += min(performance.get("rolling_sharpe", 0) * 4, 10)

        # Risk
        risk = metrics.get("risk", {})
        score += max(0, 15 - risk.get("max_drawdown", 1) * 100)
        score += max(0, 10 - risk.get("volatility", 0))
        score += max(0, 10 - risk.get("ulcer_index", 0))
        score += max(0, 10 - risk.get("cvar", 0) * 100)

        # Distributions
        distributions = metrics.get("distributions", {})
        score += max(0, 8 - abs(distributions.get("skewness", 0)))
        score += max(0, 8 - abs(distributions.get("kurtosis", 0) - 3))
        score += max(0, 8 - abs(distributions.get("tail_ratio", 1) - 1))

        # Regimes
        regimes = metrics.get("regimes", {})
        score += min(regimes.get("regime_fragility", 0) * 15, 15)

        return min(score, 100)

    # =========================================================
    # ROBUSTNESS (robustness/*)
    # =========================================================

    @staticmethod
    def _score_robustness(data: Dict[str, Any]) -> float:
        score = 0.0
        score += min(data.get("stability_score", 0) * 30, 30)
        score += min(data.get("noise_stability", 0) * 20, 20)
        score += min(data.get("monte_carlo_stability", 0) * 20, 20)
        score += min(data.get("regime_stability", 0) * 20, 20)
        return min(score, 90)

    # =========================================================
    # PORTFOLIO (portfolio/*)
    # =========================================================

    @staticmethod
    def _score_portfolio(data: Dict[str, Any]) -> float:
        score = 0.0
        score += max(0, 15 - data.get("average_correlation", 1) * 15)
        score += min(data.get("diversification_ratio", 0) * 10, 15)
        score += min(data.get("effective_number_of_bets", 0) * 2, 15)
        score += min(data.get("portfolio_fragility_index", 0) * 10, 15)
        return min(score, 60)

    # =========================================================
    # CAPITAL (capital/*)
    # =========================================================

    @staticmethod
    def _score_capital(data: Dict[str, Any]) -> float:
        score = 0.0
        score += min(data.get("kelly_fraction", 0) * 20, 20)
        score += min(data.get("risk_budgeting_score", 0) * 20, 20)
        score += min(data.get("capital_efficiency", 0) * 20, 20)
        return min(score, 60)

    # =========================================================
    # RISK CONTROL (risk_control/*)
    # =========================================================

    @staticmethod
    def _score_risk_control(data: Dict[str, Any]) -> float:
        score = 0.0
        score += min(data.get("kill_switch_score", 0) * 20, 20)
        score += min(data.get("capital_throttle_score", 0) * 20, 20)
        score += min(data.get("throttle_effectiveness", 0) * 20, 20)
        return min(score, 60)

    # =========================================================
    # STRESS (stress/*)
    # =========================================================

    @staticmethod
    def _score_stress(data: Dict[str, Any]) -> float:
        return max(0, 40 - data.get("stress_score", 0) * 40)

    # =========================================================
    # SURVIVAL (survival/*)
    # =========================================================

    @staticmethod
    def _score_survival(data: Dict[str, Any]) -> float:
        score = 0.0
        score += max(0, 20 - data.get("risk_of_ruin", 1) * 100)
        score += min(data.get("survival_score", 0) * 30, 30)
        score += min(data.get("fragility_score", 0) * 20, 20)
        return min(score, 70)

    # =========================================================
    # AGGREGATION
    # =========================================================

    @staticmethod
    def _aggregate(category_scores: Dict[str, float]) -> float:
        total = sum(category_scores.values())
        return min(total / 5, 100)

    # =========================================================
    # TIER RESOLUTION
    # =========================================================

    @classmethod
    def _resolve_tier(cls, score: float) -> GovernanceTier:
        for tier in reversed(cls.TIERS):
            if score >= tier.min_score:
                return tier
        return cls.TIERS[0]