from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SEVERITY_LEVELS = ("low", "medium", "high", "critical")
CONFIDENCE_LEVELS = ("low", "medium", "high")
RECOMMENDATION_PRIORITIES = ("now", "soon", "later")


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Invalid {field_name}: {value}")
    return value


@dataclass(frozen=True)
class InsightEvidence:
    label: str
    value: str
    comparison: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("InsightEvidence requires label")
        if not self.value:
            raise ValueError("InsightEvidence requires value")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "comparison": self.comparison,
        }


@dataclass(frozen=True)
class InsightDrilldown:
    view: str
    dashboard_filters_patch: Dict[str, Any] = field(default_factory=dict)
    dashboard_focus_group: Optional[str] = None
    dashboard_focus_chart: Optional[str] = None
    journal_search_text: Optional[str] = None
    missed_opportunity_search_text: Optional[str] = None
    selected_trade_id: Optional[str] = None
    selected_day: Optional[str] = None
    calendar_visible_month: Optional[int] = None
    calendar_visible_year: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.view:
            raise ValueError("InsightDrilldown requires view")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view": self.view,
            "dashboard_filters_patch": dict(self.dashboard_filters_patch),
            "dashboard_focus_group": self.dashboard_focus_group,
            "dashboard_focus_chart": self.dashboard_focus_chart,
            "journal_search_text": self.journal_search_text,
            "missed_opportunity_search_text": self.missed_opportunity_search_text,
            "selected_trade_id": self.selected_trade_id,
            "selected_day": self.selected_day,
            "calendar_visible_month": self.calendar_visible_month,
            "calendar_visible_year": self.calendar_visible_year,
        }


@dataclass(frozen=True)
class InsightFinding:
    title: str
    explanation: str
    categories: List[str]
    dimensions: List[str]
    severity: str
    confidence: str
    sample_size: int
    impact_score: float
    priority_score: float
    evidence: List[InsightEvidence] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    impact_description: Optional[str] = None
    behavior_tags: List[str] = field(default_factory=list)
    drilldown: Optional[InsightDrilldown] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", _validate_choice(self.severity, SEVERITY_LEVELS, "severity"))
        object.__setattr__(self, "confidence", _validate_choice(self.confidence, CONFIDENCE_LEVELS, "confidence"))
        if not self.title:
            raise ValueError("InsightFinding requires title")
        if not self.explanation:
            raise ValueError("InsightFinding requires explanation")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "explanation": self.explanation,
            "categories": list(self.categories),
            "dimensions": list(self.dimensions),
            "behavior_tags": list(self.behavior_tags),
            "severity": self.severity,
            "confidence": self.confidence,
            "sample_size": self.sample_size,
            "impact_score": self.impact_score,
            "priority_score": self.priority_score,
            "evidence": [item.to_dict() for item in self.evidence],
            "impact_description": self.impact_description,
            "drilldown": self.drilldown.to_dict() if self.drilldown else None,
        }


@dataclass(frozen=True)
class Recommendation:
    title: str
    action: str
    why: str
    implementation: List[str]
    priority: str
    source_insight_ids: List[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expected_benefit: Optional[str] = None
    drilldown: Optional[InsightDrilldown] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "priority", _validate_choice(self.priority, RECOMMENDATION_PRIORITIES, "priority"))
        if not self.title:
            raise ValueError("Recommendation requires title")
        if not self.action:
            raise ValueError("Recommendation requires action")
        if not self.why:
            raise ValueError("Recommendation requires why")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "action": self.action,
            "why": self.why,
            "implementation": list(self.implementation),
            "priority": self.priority,
            "source_insight_ids": list(self.source_insight_ids),
            "expected_benefit": self.expected_benefit,
            "drilldown": self.drilldown.to_dict() if self.drilldown else None,
        }


@dataclass
class SectionReview:
    what_is_going_wrong: List[InsightFinding] = field(default_factory=list)
    why_it_is_going_wrong: List[InsightFinding] = field(default_factory=list)
    what_is_going_right: List[InsightFinding] = field(default_factory=list)
    what_to_do_next: List[Recommendation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "what_is_going_wrong": [item.to_dict() for item in self.what_is_going_wrong],
            "why_it_is_going_wrong": [item.to_dict() for item in self.why_it_is_going_wrong],
            "what_is_going_right": [item.to_dict() for item in self.what_is_going_right],
            "what_to_do_next": [item.to_dict() for item in self.what_to_do_next],
        }


@dataclass(frozen=True)
class DashboardMetricReview:
    metric_key: str
    label: str
    meaning: str
    current_value_summary: str
    what_it_shows: str
    status: str = "unknown"
    healthy_range: Optional[str] = None
    satisfactory_range: Optional[str] = None
    weak_range: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_key": self.metric_key,
            "label": self.label,
            "meaning": self.meaning,
            "current_value_summary": self.current_value_summary,
            "what_it_shows": self.what_it_shows,
            "healthy_range": self.healthy_range,
            "satisfactory_range": self.satisfactory_range,
            "weak_range": self.weak_range,
            "status": self.status,
        }


@dataclass(frozen=True)
class DashboardChartReview:
    chart_key: str
    label: str
    meaning: str
    what_it_shows: str
    important_takeaway: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_key": self.chart_key,
            "label": self.label,
            "meaning": self.meaning,
            "what_it_shows": self.what_it_shows,
            "important_takeaway": self.important_takeaway,
        }


@dataclass
class DashboardDetailedReview:
    metric_reviews: List[DashboardMetricReview] = field(default_factory=list)
    chart_reviews: List[DashboardChartReview] = field(default_factory=list)
    what_is_going_wrong: List[InsightFinding] = field(default_factory=list)
    why_it_is_going_wrong: List[InsightFinding] = field(default_factory=list)
    what_is_going_right: List[InsightFinding] = field(default_factory=list)
    what_to_do_next: List[Recommendation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_reviews": [item.to_dict() for item in self.metric_reviews],
            "chart_reviews": [item.to_dict() for item in self.chart_reviews],
            "what_is_going_wrong": [item.to_dict() for item in self.what_is_going_wrong],
            "why_it_is_going_wrong": [item.to_dict() for item in self.why_it_is_going_wrong],
            "what_is_going_right": [item.to_dict() for item in self.what_is_going_right],
            "what_to_do_next": [item.to_dict() for item in self.what_to_do_next],
        }


@dataclass(frozen=True)
class AIInsightsMetadata:
    account_id: str
    generated_at: str
    trade_count: int
    closed_trade_count: int
    missed_opportunity_count: int
    visible_period: Dict[str, Optional[str]]
    analysis_stage: str = "scaffold"
    data_coverage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "generated_at": self.generated_at,
            "trade_count": self.trade_count,
            "closed_trade_count": self.closed_trade_count,
            "missed_opportunity_count": self.missed_opportunity_count,
            "visible_period": dict(self.visible_period),
            "analysis_stage": self.analysis_stage,
            "data_coverage": dict(self.data_coverage),
        }


@dataclass
class AIInsightsResponse:
    headline_summary: List[str]
    summary: SectionReview
    detailed_review: Dict[str, Any]
    metadata: AIInsightsMetadata
    created_at_epoch: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline_summary": list(self.headline_summary),
            "summary": self.summary.to_dict(),
            "detailed_review": {
                "dashboard": self.detailed_review["dashboard"].to_dict(),
                "journal": self.detailed_review["journal"].to_dict(),
                "missed_opportunities": self.detailed_review["missed_opportunities"].to_dict(),
                "calendar": self.detailed_review["calendar"].to_dict(),
            },
            "metadata": self.metadata.to_dict(),
            "created_at_epoch": self.created_at_epoch,
        }
