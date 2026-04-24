from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from ai.insights_models import InsightDrilldown, InsightEvidence, InsightFinding, Recommendation


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE_ORDER = {"low": 1, "medium": 2, "high": 3}
RECOMMENDATION_ORDER = {"now": 3, "soon": 2, "later": 1}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def derive_severity(impact_score: float) -> str:
    score = _clamp(impact_score)
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def derive_confidence(sample_size: int) -> str:
    if sample_size >= 120:
        return "high"
    if sample_size >= 40:
        return "medium"
    return "low"


def compute_priority_score(severity: str, confidence: str, impact_score: float) -> float:
    sev = {  # normalized 0..1
        "low": 0.30,
        "medium": 0.55,
        "high": 0.78,
        "critical": 0.95,
    }[severity]
    conf = {
        "low": 0.35,
        "medium": 0.60,
        "high": 0.90,
    }[confidence]
    impact = _clamp(impact_score)
    return round((sev * 0.45 + conf * 0.20 + impact * 0.35) * 100.0, 2)


def build_evidence(items: Sequence[tuple[str, str, Optional[str]] | tuple[str, str]]) -> List[InsightEvidence]:
    evidence: List[InsightEvidence] = []
    for item in items:
        if len(item) == 2:
            label, value = item
            comparison = None
        else:
            label, value, comparison = item
        evidence.append(InsightEvidence(label=label, value=value, comparison=comparison))
    return evidence


def make_finding(
    *,
    title: str,
    explanation: str,
    categories: List[str],
    dimensions: List[str],
    sample_size: int,
    impact_score: float,
    evidence: List[InsightEvidence],
    behavior_tags: Optional[List[str]] = None,
    impact_description: Optional[str] = None,
    severity: Optional[str] = None,
    confidence: Optional[str] = None,
    drilldown: Optional[InsightDrilldown] = None,
) -> InsightFinding:
    score = _clamp(impact_score)
    resolved_severity = severity or derive_severity(score)
    resolved_confidence = confidence or derive_confidence(sample_size)
    priority_score = compute_priority_score(resolved_severity, resolved_confidence, score)
    return InsightFinding(
        title=title,
        explanation=explanation,
        categories=categories,
        dimensions=dimensions,
        behavior_tags=behavior_tags or [],
        severity=resolved_severity,
        confidence=resolved_confidence,
        sample_size=sample_size,
        impact_score=round(score, 3),
        priority_score=priority_score,
        evidence=evidence,
        impact_description=impact_description,
        drilldown=drilldown,
    )


def rank_findings(findings: Iterable[InsightFinding], limit: int = 3) -> List[InsightFinding]:
    ranked = sorted(
        list(findings),
        key=lambda item: (
            item.priority_score,
            item.impact_score,
            item.sample_size,
            SEVERITY_ORDER.get(item.severity, 0),
            CONFIDENCE_ORDER.get(item.confidence, 0),
        ),
        reverse=True,
    )
    return ranked[:limit]


def derive_recommendation_priority(source_findings: Sequence[InsightFinding]) -> str:
    if not source_findings:
        return "later"
    max_priority = max(finding.priority_score for finding in source_findings)
    if max_priority >= 70:
        return "now"
    if max_priority >= 45:
        return "soon"
    return "later"


def make_recommendation(
    *,
    title: str,
    action: str,
    why: str,
    implementation: List[str],
    source_findings: Sequence[InsightFinding],
    expected_benefit: Optional[str] = None,
    priority: Optional[str] = None,
    drilldown: Optional[InsightDrilldown] = None,
) -> Recommendation:
    resolved_priority = priority or derive_recommendation_priority(source_findings)
    inherited_drilldown = drilldown or next((finding.drilldown for finding in source_findings if finding.drilldown), None)
    return Recommendation(
        title=title,
        action=action,
        why=why,
        implementation=implementation,
        priority=resolved_priority,
        source_insight_ids=[finding.id for finding in source_findings],
        expected_benefit=expected_benefit,
        drilldown=inherited_drilldown,
    )


def rank_recommendations(
    items: Iterable[Recommendation],
    limit: int = 3,
    finding_lookup: Optional[Dict[str, InsightFinding]] = None,
) -> List[Recommendation]:
    def _source_priority(item: Recommendation) -> float:
        if not finding_lookup:
            return 0.0
        return max(
            (finding_lookup[source_id].priority_score for source_id in item.source_insight_ids if source_id in finding_lookup),
            default=0.0,
        )

    ranked = sorted(
        list(items),
        key=lambda item: (
            RECOMMENDATION_ORDER.get(item.priority, 0),
            _source_priority(item),
            len(item.implementation),
            1 if item.expected_benefit else 0,
            len(item.source_insight_ids),
        ),
        reverse=True,
    )
    return ranked[:limit]
