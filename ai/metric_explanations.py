from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from ai.insights_models import DashboardMetricReview


class MetricExplanationSpec(TypedDict):
    label: str
    meaning: str
    what_it_shows: str
    format: str
    healthy_range: str
    satisfactory_range: str
    weak_range: str
    status_rule: str
    good: Optional[float]
    ok: Optional[float]


METRIC_EXPLANATIONS: Dict[str, MetricExplanationSpec] = {
    "sharpe": {
        "label": "Net Sharpe",
        "meaning": "Measures return achieved per unit of total volatility.",
        "what_it_shows": "Higher values usually indicate better risk-adjusted consistency.",
        "format": "number",
        "healthy_range": "> 1.2",
        "satisfactory_range": "0.8 to 1.2",
        "weak_range": "< 0.8",
        "status_rule": "range",
        "good": 1.2,
        "ok": 0.8,
    },
    "sortino": {
        "label": "Net Sortino",
        "meaning": "Focuses on downside volatility rather than all volatility.",
        "what_it_shows": "Shows how efficiently returns are produced relative to harmful downside moves.",
        "format": "number",
        "healthy_range": "> 1.5",
        "satisfactory_range": "1.0 to 1.5",
        "weak_range": "< 1.0",
        "status_rule": "range",
        "good": 1.5,
        "ok": 1.0,
    },
    "max_drawdown": {
        "label": "Max Drawdown",
        "meaning": "Largest peak-to-trough decline in the sample period.",
        "what_it_shows": "Shows capital pain and recovery pressure during weak phases.",
        "format": "percent",
        "healthy_range": "< 10%",
        "satisfactory_range": "10% to 15%",
        "weak_range": "> 15%",
        "status_rule": "inverse_range",
        "good": 0.10,
        "ok": 0.15,
    },
    "profit_factor": {
        "label": "Profit Factor",
        "meaning": "Gross profit divided by gross loss.",
        "what_it_shows": "Values above 1 indicate gross gains exceed gross losses.",
        "format": "number",
        "healthy_range": "> 1.3",
        "satisfactory_range": "1.0 to 1.3",
        "weak_range": "< 1.0",
        "status_rule": "range",
        "good": 1.3,
        "ok": 1.0,
    },
    "expectancy": {
        "label": "Expectancy",
        "meaning": "Average expected return per trade after win/loss behavior.",
        "what_it_shows": "Positive values suggest strategy decisions are additive over time.",
        "format": "number",
        "healthy_range": "> 0",
        "satisfactory_range": "Near 0",
        "weak_range": "< 0",
        "status_rule": "sign",
        "good": None,
        "ok": None,
    },
    "win_rate": {
        "label": "Win Rate",
        "meaning": "Percentage of closed trades that ended positive.",
        "what_it_shows": "Useful only when interpreted alongside payoff ratio and expectancy.",
        "format": "percent",
        "healthy_range": "Contextual",
        "satisfactory_range": "Contextual",
        "weak_range": "Contextual",
        "status_rule": "contextual",
        "good": None,
        "ok": None,
    },
    "payoff_ratio": {
        "label": "Payoff Ratio",
        "meaning": "Average winner size divided by average loser size.",
        "what_it_shows": "Shows whether winners are large enough to support the current win rate.",
        "format": "number",
        "healthy_range": "> 1.4",
        "satisfactory_range": "1.0 to 1.4",
        "weak_range": "< 1.0",
        "status_rule": "range",
        "good": 1.4,
        "ok": 1.0,
    },
    "calmar": {
        "label": "Net Calmar",
        "meaning": "Compares annualized return to maximum drawdown.",
        "what_it_shows": "Tells how efficiently returns are being generated relative to deep equity setbacks.",
        "format": "number",
        "healthy_range": "> 1.0",
        "satisfactory_range": "0.5 to 1.0",
        "weak_range": "< 0.5",
        "status_rule": "range",
        "good": 1.0,
        "ok": 0.5,
    },
    "cagr": {
        "label": "Net CAGR",
        "meaning": "Annualized compounded return over the measured period.",
        "what_it_shows": "Summarizes growth rate, but should always be read together with drawdown and volatility.",
        "format": "percent",
        "healthy_range": "> 15%",
        "satisfactory_range": "5% to 15%",
        "weak_range": "< 5%",
        "status_rule": "range",
        "good": 0.15,
        "ok": 0.05,
    },
}


def build_dashboard_metric_review(metric_key: str, value: Any) -> DashboardMetricReview:
    spec = METRIC_EXPLANATIONS[metric_key]
    numeric = _to_number(value)
    return DashboardMetricReview(
        metric_key=metric_key,
        label=spec["label"],
        meaning=spec["meaning"],
        current_value_summary=_format_value(numeric, spec["format"]),
        what_it_shows=spec["what_it_shows"],
        healthy_range=spec["healthy_range"],
        satisfactory_range=spec["satisfactory_range"],
        weak_range=spec["weak_range"],
        status=_derive_status(
            numeric,
            rule=spec["status_rule"],
            good=spec["good"],
            ok=spec["ok"],
        ),
    )


def build_dashboard_metric_reviews(items: List[tuple[str, Any]]) -> List[DashboardMetricReview]:
    reviews: List[DashboardMetricReview] = []
    for metric_key, value in items:
        if metric_key not in METRIC_EXPLANATIONS:
            continue
        reviews.append(build_dashboard_metric_review(metric_key, value))
    return reviews


def _to_number(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _format_value(value: Optional[float], format_kind: str) -> str:
    if value is None:
        return "n/a"
    if format_kind == "percent":
        return f"{value * 100:.2f}%"
    return f"{value:.3f}"


def _derive_status(
    value: Optional[float],
    *,
    rule: str,
    good: Optional[float],
    ok: Optional[float],
) -> str:
    if value is None:
        return "unknown"
    if rule == "range":
        assert good is not None and ok is not None
        if value >= good:
            return "good"
        if value >= ok:
            return "satisfactory"
        return "bad"
    if rule == "inverse_range":
        assert good is not None and ok is not None
        if value <= good:
            return "good"
        if value <= ok:
            return "satisfactory"
        return "bad"
    if rule == "sign":
        if value > 0:
            return "good"
        if value == 0:
            return "satisfactory"
        return "bad"
    return "unknown"
