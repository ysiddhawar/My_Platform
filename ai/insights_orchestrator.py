from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.context import Context

from ai.analyzers import (
    CalendarInsightAnalyzer,
    CrossReferenceInsightAnalyzer,
    DashboardInsightAnalyzer,
    JournalInsightAnalyzer,
    MissedOpportunityInsightAnalyzer,
    RecommendationEngine,
)
from ai.insight_scoring import rank_findings, rank_recommendations
from ai.insight_scoring import CONFIDENCE_ORDER, SEVERITY_ORDER
from ai.insights_models import (
    AIInsightMetricProjection,
    AIInsightProjectionGroup,
    AIInsightSummaryTabs,
    AIInsightTabCard,
    AIInsightsMetadata,
    AIInsightsResponse,
    DashboardDetailedReview,
    InsightEvidence,
    InsightFinding,
    Recommendation,
    SectionReview,
)


INSIGHT_METRIC_CATEGORIES = (
    "journal",
    "performance",
    "risk",
    "distributions",
    "regimes",
    "robustness",
    "portfolio",
    "capital",
    "risk_control",
    "stress",
    "survival",
)
SUMMARY_MIN_PRIORITY = 40.0


class AIInsightsOrchestrator:
    """
    Unified account-data aggregation and section-analysis orchestration.

    Phase 4: each sidebar section now has a dedicated analyzer that produces
    scored findings and traceable recommendations, and the orchestrator merges
    them into both top-level summary and detailed-review sections.
    """

    def __init__(
        self,
        trade_repository,
        missed_opportunity_repository,
        trading_platform_session_repository,
        behavioral_analyzer,
        calendar_aggregation_engine,
        execution_engine,
        registry,
        account_repository=None,
        dashboard_analyzer: Optional[DashboardInsightAnalyzer] = None,
        journal_analyzer: Optional[JournalInsightAnalyzer] = None,
        missed_opportunity_analyzer: Optional[MissedOpportunityInsightAnalyzer] = None,
        calendar_analyzer: Optional[CalendarInsightAnalyzer] = None,
        cross_reference_analyzer: Optional[CrossReferenceInsightAnalyzer] = None,
        recommendation_engine: Optional[RecommendationEngine] = None,
    ) -> None:
        self.trade_repository = trade_repository
        self.missed_opportunity_repository = missed_opportunity_repository
        self.trading_platform_session_repository = trading_platform_session_repository
        self.behavioral_analyzer = behavioral_analyzer
        self.calendar_aggregation_engine = calendar_aggregation_engine
        self.execution_engine = execution_engine
        self.registry = registry
        self.account_repository = account_repository
        self.dashboard_analyzer = dashboard_analyzer or DashboardInsightAnalyzer()
        self.journal_analyzer = journal_analyzer or JournalInsightAnalyzer()
        self.missed_opportunity_analyzer = missed_opportunity_analyzer or MissedOpportunityInsightAnalyzer()
        self.calendar_analyzer = calendar_analyzer or CalendarInsightAnalyzer()
        self.cross_reference_analyzer = cross_reference_analyzer or CrossReferenceInsightAnalyzer()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def run(self, account_id: str, lookback: Optional[int] = None) -> AIInsightsResponse:
        context = self._build_unified_context(account_id=account_id, lookback=lookback)

        analyses = {
            "dashboard": self.dashboard_analyzer.analyze(context),
            "journal": self.journal_analyzer.analyze(context),
            "missed_opportunities": self.missed_opportunity_analyzer.analyze(context),
            "calendar": self.calendar_analyzer.analyze(context),
            "cross_reference": self.cross_reference_analyzer.analyze(context),
        }
        recommendation_outputs = self.recommendation_engine.generate(
            context=context,
            analyses=analyses,
        )

        summary = self._build_summary(
            analyses=analyses,
            summary_recommendations=recommendation_outputs["summary"],
        )
        summary_tabs = self._build_summary_tabs(
            analyses=analyses,
            recommendations=recommendation_outputs["summary"],
            context=context,
        )

        detailed_review = {
            "dashboard": DashboardDetailedReview(
                metric_reviews=analyses["dashboard"].get("metric_reviews", []),
                chart_reviews=analyses["dashboard"].get("chart_reviews", []),
                what_is_going_wrong=rank_findings(analyses["dashboard"].get("wrong", []), limit=8),
                why_it_is_going_wrong=rank_findings(analyses["dashboard"].get("why", []), limit=8),
                what_is_going_right=rank_findings(analyses["dashboard"].get("right", []), limit=8),
                what_to_do_next=recommendation_outputs["sections"]["dashboard"],
            ),
            "journal": self._section_from_analysis(
                analyses["journal"],
                recommendations=recommendation_outputs["sections"]["journal"],
            ),
            "missed_opportunities": self._section_from_analysis(
                analyses["missed_opportunities"],
                recommendations=recommendation_outputs["sections"]["missed_opportunities"],
            ),
            "calendar": self._section_from_analysis(
                analyses["calendar"],
                recommendations=recommendation_outputs["sections"]["calendar"],
            ),
        }

        metadata = AIInsightsMetadata(
            account_id=account_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            trade_count=len(context["trades"]),
            closed_trade_count=len(context["closed_trades"]),
            missed_opportunity_count=len(context["missed_opportunities"]),
            visible_period=context["visible_period"],
            analysis_stage="validation_tuned",
            data_coverage={
                "calendar_days": len(context["calendar_summaries"]),
                "session_count": len(context["platform_sessions"]),
                "behavior_signal_count": len(context["behavior_analysis"].get("signals", {})),
                "metric_categories": sorted(context["metrics_by_category"].keys()),
                "metric_error_categories": sorted(key for key, value in context["metric_errors"].items() if value),
                "section_output_counts": {
                    "dashboard": self._count_section_outputs(analyses["dashboard"]),
                    "journal": self._count_section_outputs(analyses["journal"]),
                    "missed_opportunities": self._count_section_outputs(analyses["missed_opportunities"]),
                    "calendar": self._count_section_outputs(analyses["calendar"]),
                    "cross_reference": self._count_section_outputs(analyses["cross_reference"]),
                },
                "summary_counts": {
                    "wrong": len(summary.what_is_going_wrong),
                    "why": len(summary.why_it_is_going_wrong),
                    "right": len(summary.what_is_going_right),
                    "recommendations": len(summary.what_to_do_next),
                },
                "sources": {
                    "dashboard_metrics": bool(context["metrics_by_category"]),
                    "journal": len(context["trades"]) > 0,
                    "calendar": len(context["calendar_summaries"]) > 0,
                    "missed_opportunities": len(context["missed_opportunities"]) > 0,
                    "sessions": len(context["platform_sessions"]) > 0,
                    "behavior": bool(context["behavior_analysis"].get("signals")),
                },
            },
        )

        return AIInsightsResponse(
            headline_summary=self._build_headline_summary(summary),
            summary=summary,
            summary_tabs=summary_tabs,
            detailed_review=detailed_review,
            metadata=metadata,
        )

    def _build_summary_tabs(
        self,
        *,
        analyses: Dict[str, Dict[str, Any]],
        recommendations,
        context: Dict[str, Any],
    ) -> AIInsightSummaryTabs:
        wrong_findings: list[InsightFinding] = []
        why_findings: list[InsightFinding] = []
        right_findings: list[InsightFinding] = []
        finding_lookup: dict[str, InsightFinding] = {}

        for analysis in analyses.values():
            wrong_findings.extend(analysis.get("wrong", []))
            why_findings.extend(analysis.get("why", []))
            right_findings.extend(analysis.get("right", []))

        for finding in wrong_findings + why_findings + right_findings:
            finding_lookup[finding.id] = finding

        bad_ranked = sorted(
            wrong_findings,
            key=lambda item: (
                SEVERITY_ORDER.get(item.severity, 0),
                item.priority_score,
                item.impact_score,
                item.sample_size,
                CONFIDENCE_ORDER.get(item.confidence, 0),
            ),
            reverse=True,
        )[:15]
        good_ranked = rank_findings(right_findings, limit=15)
        recommended_ranked = rank_recommendations(recommendations, limit=15, finding_lookup=finding_lookup)
        projection_context = self._build_projection_context(context)

        return AIInsightSummaryTabs(
            bad=[
                self._finding_to_bad_card(
                    finding=finding,
                    why_finding=self._match_why_finding(finding, why_findings),
                    context=context,
                    projection_context=projection_context,
                )
                for finding in bad_ranked
            ],
            good=[
                self._finding_to_good_card(
                    finding,
                    context=context,
                    projection_context=projection_context,
                )
                for finding in good_ranked
            ],
            recommended=[
                self._recommendation_to_card(
                    recommendation,
                    finding_lookup,
                    context=context,
                    projection_context=projection_context,
                )
                for recommendation in recommended_ranked
            ],
        )

    def _match_why_finding(
        self,
        finding: InsightFinding,
        why_findings: list[InsightFinding],
    ) -> Optional[InsightFinding]:
        if not why_findings:
            return None
        finding_categories = set(finding.categories)
        finding_dimensions = set(finding.dimensions)

        def _score(candidate: InsightFinding) -> tuple[int, float, float]:
            category_overlap = len(finding_categories.intersection(candidate.categories))
            dimension_overlap = len(finding_dimensions.intersection(candidate.dimensions))
            return (category_overlap + dimension_overlap, candidate.priority_score, candidate.impact_score)

        best = max(why_findings, key=_score)
        return best if _score(best)[0] > 0 else rank_findings(why_findings, limit=1)[0]

    def _finding_to_bad_card(
        self,
        *,
        finding: InsightFinding,
        why_finding: Optional[InsightFinding],
        context: Dict[str, Any],
        projection_context: Dict[str, Any],
    ) -> AIInsightTabCard:
        why = why_finding.explanation if why_finding else "The pattern is strong enough in your data to deserve focused review before increasing risk."
        impact = self._impact_percent(finding)
        basis_label, basis_count = self._confidence_basis_for_finding(finding=finding, context=context)
        return AIInsightTabCard(
            id=finding.id,
            title=finding.title,
            main_point=finding.explanation,
            why=why,
            evidence_highlights=self._evidence_highlights(finding, why_finding),
            projected_effect=(
                f"If this continues, the same behavior can keep dragging expectancy, drawdown, or consistency. "
                f"If fixed, the projection compares the current account metrics against a conservative improvement model."
            ),
            projection_groups=self._projection_groups(
                projection_context=projection_context,
                modes=[("continued", "bad_continued"), ("fixed", "bad_fixed")],
                impact_score=finding.impact_score,
            ),
            confidence=finding.confidence,
            sample_size=basis_count,
            confidence_basis_label=basis_label,
            confidence_basis_count=basis_count,
            severity=finding.severity,
        )

    def _finding_to_good_card(
        self,
        finding: InsightFinding,
        *,
        context: Dict[str, Any],
        projection_context: Dict[str, Any],
    ) -> AIInsightTabCard:
        impact = self._impact_percent(finding)
        basis_label, basis_count = self._confidence_basis_for_finding(finding=finding, context=context)
        return AIInsightTabCard(
            id=finding.id,
            title=finding.title,
            main_point=finding.explanation,
            why=finding.impact_description or "This positive pattern appears repeatable enough to protect while improving weaker areas.",
            evidence_highlights=self._evidence_highlights(finding),
            projected_effect=(
                f"If you keep this behavior stable, it can protect the part of your trading that is already working "
                f"while the projection shows how core account metrics could hold or improve."
            ),
            projection_groups=self._projection_groups(
                projection_context=projection_context,
                modes=[("continued", "good_continued")],
                impact_score=finding.impact_score,
            ),
            confidence=finding.confidence,
            sample_size=basis_count,
            confidence_basis_label=basis_label,
            confidence_basis_count=basis_count,
        )

    def _recommendation_to_card(
        self,
        recommendation: Recommendation,
        finding_lookup: dict[str, InsightFinding],
        *,
        context: Dict[str, Any],
        projection_context: Dict[str, Any],
    ) -> AIInsightTabCard:
        source_findings = [
            finding_lookup[source_id]
            for source_id in recommendation.source_insight_ids
            if source_id in finding_lookup
        ]
        strongest_source = rank_findings(source_findings, limit=1)[0] if source_findings else None
        confidence = self._strongest_confidence(source_findings)
        basis_label, basis_count = self._confidence_basis_for_recommendation(source_findings, context)
        source_impact_score = strongest_source.impact_score if strongest_source else 0.25
        evidence = self._evidence_highlights(strongest_source) if strongest_source else []

        return AIInsightTabCard(
            id=recommendation.id,
            title=recommendation.title,
            main_point=recommendation.action,
            why=recommendation.why,
            evidence_highlights=evidence,
            projected_effect=recommendation.expected_benefit or "This focus area should improve long-term trading quality if the underlying evidence remains stable.",
            projection_groups=self._projection_groups(
                projection_context=projection_context,
                modes=[("long_term", "recommended_long_term")],
                impact_score=source_impact_score,
            ),
            confidence=confidence,
            sample_size=basis_count,
            confidence_basis_label=basis_label,
            confidence_basis_count=basis_count,
            priority=recommendation.priority,
        )

    def _evidence_highlights(
        self,
        finding: Optional[InsightFinding],
        secondary: Optional[InsightFinding] = None,
        *,
        limit: int = 3,
    ) -> list[InsightEvidence]:
        if finding is None:
            return []
        highlights: list[InsightEvidence] = []
        seen: set[tuple[str, str]] = set()
        for source in (finding, secondary):
            if source is None:
                continue
            for item in source.evidence:
                key = (item.label, item.value)
                if key in seen:
                    continue
                seen.add(key)
                highlights.append(item)
                if len(highlights) >= limit:
                    return highlights
        return highlights

    def _confidence_basis_for_finding(
        self,
        *,
        finding: InsightFinding,
        context: Dict[str, Any],
    ) -> tuple[str, int]:
        categories = set(finding.categories)
        dimensions = set(finding.dimensions)
        if "missed_opportunities" in categories or "missed_opportunity" in categories:
            return "missed opportunities", len(context.get("missed_opportunities", []))
        if "calendar" in categories or "day" in dimensions:
            return "calendar days", len(context.get("calendar_summaries", []))
        if "session" in dimensions or "time" in dimensions:
            return "platform sessions", len(context.get("platform_sessions", []))
        return "closed trades", len(context.get("closed_trades", []))

    def _confidence_basis_for_recommendation(
        self,
        source_findings: list[InsightFinding],
        context: Dict[str, Any],
    ) -> tuple[str, int]:
        if not source_findings:
            return "closed trades", len(context.get("closed_trades", []))
        basis_counts: dict[str, int] = {}
        for finding in source_findings:
            label, count = self._confidence_basis_for_finding(finding=finding, context=context)
            basis_counts[label] = max(count, basis_counts.get(label, 0))
        return max(basis_counts.items(), key=lambda item: item[1])

    def _build_projection_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        closed_trades = sorted(
            [trade for trade in context.get("closed_trades", []) if trade.get("is_closed")],
            key=self._trade_close_key,
        )
        capital = self._derive_account_capital(context, closed_trades)
        return {
            "closed_trades": closed_trades,
            "capital": capital,
            "current": self._projection_stats(closed_trades, capital=capital),
        }

    def _projection_groups(
        self,
        *,
        projection_context: Dict[str, Any],
        modes: list[tuple[str, str]],
        impact_score: float,
    ) -> list[AIInsightProjectionGroup]:
        groups: list[AIInsightProjectionGroup] = []
        for group_key, projection_mode in modes:
            metrics = self._metric_projections(
                projection_context=projection_context,
                projection_mode=projection_mode,
                impact_score=impact_score,
            )
            if metrics:
                groups.append(AIInsightProjectionGroup(key=group_key, metrics=metrics))
        return groups

    def _metric_projections(
        self,
        *,
        projection_context: Dict[str, Any],
        projection_mode: str,
        impact_score: float,
    ) -> list[AIInsightMetricProjection]:
        current = projection_context["current"]
        trades = projection_context["closed_trades"]
        capital = projection_context["capital"]
        if not trades:
            return []

        projected_trades = self._projected_trade_values(trades, projection_mode, impact_score)
        projected = self._projection_stats(projected_trades, capital=capital)
        metrics: list[AIInsightMetricProjection] = []

        metrics.extend(
            self._curve_projection("net_pnl_curve", "Net P&L Curve", current, projected, "net_pnl_curve", "$")
        )
        metrics.extend(
            self._curve_projection("equity_curve", "Equity Curve", current, projected, "equity_curve", "$")
        )
        weekday = self._weekday_projection(current, projected)
        if weekday:
            metrics.append(weekday)

        scalar_specs = [
            ("profit_factor", "Profit Factor", "number", False),
            ("expectancy", "Expectancy", "currency", False),
            ("max_drawdown", "Max Drawdown", "percent", True),
            ("payoff_ratio", "Payoff Ratio", "number", False),
            ("avg_win", "Avg Win", "currency", False),
            ("avg_loss", "Avg Loss", "currency", True),
            ("net_roi", "Net ROI", "percent", False),
            ("r_multiple", "R Multiple", "number", False),
            ("rrr", "R:R", "number", False),
            ("win_pct", "Win %", "percent", False),
            ("loss_pct", "Loss %", "percent", True),
        ]
        for metric_key, label, value_type, lower_is_better in scalar_specs:
            projection = self._scalar_projection(
                metric_key=metric_key,
                label=label,
                current_value=current.get(metric_key),
                projected_value=projected.get(metric_key),
                value_type=value_type,
                lower_is_better=lower_is_better,
            )
            if projection:
                metrics.append(projection)

        return metrics

    def _projected_trade_values(
        self,
        trades: list[Dict[str, Any]],
        mode: str,
        impact_score: float,
    ) -> list[Dict[str, Any]]:
        impact = max(0.05, min(0.75, float(impact_score or 0.25)))
        projected: list[Dict[str, Any]] = []
        for trade in trades:
            item = dict(trade)
            pnl = self._to_float(trade.get("net_pnl"))
            r_multiple = self._to_float(trade.get("r_multiple"))
            rrr = self._to_float(trade.get("rrr_at_entry"))

            if mode == "bad_continued":
                pnl_factor = 0.94 if pnl > 0 else 1.0 + impact * 0.45
                r_factor = 0.96 if (r_multiple or 0.0) > 0 else 1.0 + impact * 0.35
            elif mode == "bad_fixed":
                pnl_factor = 1.04 if pnl > 0 else max(0.35, 1.0 - impact * 0.55)
                r_factor = 1.05 if (r_multiple or 0.0) > 0 else max(0.45, 1.0 - impact * 0.5)
            elif mode == "good_continued":
                pnl_factor = 1.0 + impact * 0.18 if pnl > 0 else max(0.75, 1.0 - impact * 0.16)
                r_factor = 1.0 + impact * 0.12 if (r_multiple or 0.0) > 0 else max(0.85, 1.0 - impact * 0.08)
            else:
                pnl_factor = 1.0 + impact * 0.22 if pnl > 0 else max(0.55, 1.0 - impact * 0.28)
                r_factor = 1.0 + impact * 0.14 if (r_multiple or 0.0) > 0 else max(0.7, 1.0 - impact * 0.18)

            item["net_pnl"] = pnl * pnl_factor
            if r_multiple is not None:
                item["r_multiple"] = r_multiple * r_factor
            if rrr is not None and mode != "bad_continued":
                item["rrr_at_entry"] = rrr * (1.0 + impact * 0.08)
            elif rrr is not None:
                item["rrr_at_entry"] = rrr * max(0.85, 1.0 - impact * 0.08)
            projected.append(item)
        return projected

    def _projection_stats(self, trades: list[Dict[str, Any]], *, capital: float) -> Dict[str, Any]:
        pnls = [self._to_float(trade.get("net_pnl")) for trade in trades]
        wins = [value for value in pnls if value > 0]
        losses = [value for value in pnls if value <= 0]
        total_pnl = sum(pnls)
        equity_curve: list[float] = []
        net_pnl_curve: list[float] = []
        weekday_pnl: dict[str, float] = defaultdict(float)
        running = capital
        running_pnl = 0.0
        labels: list[str] = []

        for index, trade in enumerate(trades):
            pnl = self._to_float(trade.get("net_pnl"))
            running += pnl
            running_pnl += pnl
            equity_curve.append(round(running, 2))
            net_pnl_curve.append(round(running_pnl, 2))
            labels.append(self._short_trade_label(trade, index))
            weekday = self._trade_weekday(trade)
            if weekday:
                weekday_pnl[weekday] += pnl

        avg_win = sum(wins) / len(wins) if wins else None
        avg_loss = sum(losses) / len(losses) if losses else None
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        r_values = [self._to_float(trade.get("r_multiple")) for trade in trades if trade.get("r_multiple") is not None]
        rrr_values = [self._to_float(trade.get("rrr_at_entry")) for trade in trades if trade.get("rrr_at_entry") is not None]
        return {
            "capital": capital,
            "net_pnl": total_pnl,
            "net_pnl_curve": net_pnl_curve,
            "equity_curve": equity_curve,
            "curve_labels": labels,
            "weekday_pnl": dict(weekday_pnl),
            "profit_factor": gross_win / gross_loss if gross_loss else None,
            "expectancy": total_pnl / len(pnls) if pnls else None,
            "max_drawdown": self._max_drawdown(equity_curve),
            "payoff_ratio": abs(avg_win / avg_loss) if avg_win is not None and avg_loss not in (None, 0) else None,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "net_roi": total_pnl / capital if capital else None,
            "r_multiple": sum(r_values) / len(r_values) if r_values else None,
            "rrr": sum(rrr_values) / len(rrr_values) if rrr_values else None,
            "win_pct": len(wins) / len(pnls) if pnls else None,
            "loss_pct": len(losses) / len(pnls) if pnls else None,
        }

    def _curve_projection(
        self,
        metric_key: str,
        label: str,
        current: Dict[str, Any],
        projected: Dict[str, Any],
        stats_key: str,
        prefix: str,
    ) -> list[AIInsightMetricProjection]:
        current_points = current.get(stats_key) or []
        projected_points = projected.get(stats_key) or []
        if len(current_points) < 2 or len(projected_points) < 2:
            return []
        current_end = current_points[-1]
        projected_end = projected_points[-1]
        return [
            AIInsightMetricProjection(
                metric_key=metric_key,
                label=label,
                current_value=self._format_currency(current_end) if prefix == "$" else str(current_end),
                projected_value=self._format_currency(projected_end) if prefix == "$" else str(projected_end),
                delta_label=self._format_currency_delta(projected_end - current_end),
                direction=self._direction(projected_end, current_end),
                visual_type="curve",
                baseline_points=self._thin_points(current_points),
                points=self._thin_points(projected_points),
                labels=self._thin_labels(current.get("curve_labels") or [], len(self._thin_points(projected_points))),
            )
        ]

    def _weekday_projection(
        self,
        current: Dict[str, Any],
        projected: Dict[str, Any],
    ) -> Optional[AIInsightMetricProjection]:
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        current_values = [round(float((current.get("weekday_pnl") or {}).get(day, 0.0)), 2) for day in weekdays]
        projected_values = [round(float((projected.get("weekday_pnl") or {}).get(day, 0.0)), 2) for day in weekdays]
        if not any(current_values) and not any(projected_values):
            return None
        current_total = sum(current_values)
        projected_total = sum(projected_values)
        return AIInsightMetricProjection(
            metric_key="pnl_by_weekday",
            label="P&L by Weekday",
            current_value=self._format_currency(current_total),
            projected_value=self._format_currency(projected_total),
            delta_label=self._format_currency_delta(projected_total - current_total),
            direction=self._direction(projected_total, current_total),
            visual_type="weekday_bar",
            baseline_points=current_values,
            points=projected_values,
            labels=[day[:3] for day in weekdays],
        )

    def _scalar_projection(
        self,
        *,
        metric_key: str,
        label: str,
        current_value: Optional[float],
        projected_value: Optional[float],
        value_type: str,
        lower_is_better: bool,
    ) -> Optional[AIInsightMetricProjection]:
        if current_value is None or projected_value is None:
            return None
        delta = projected_value - current_value
        direction = self._direction(projected_value, current_value, lower_is_better=lower_is_better)
        return AIInsightMetricProjection(
            metric_key=metric_key,
            label=label,
            current_value=self._format_projection_value(current_value, value_type),
            projected_value=self._format_projection_value(projected_value, value_type),
            delta_label=self._format_projection_delta(delta, value_type),
            direction=direction,
            visual_type="metric",
            baseline_points=[round(float(current_value), 4)],
            points=[round(float(projected_value), 4)],
        )

    def _impact_percent(self, finding: Optional[InsightFinding]) -> int:
        if finding is None:
            return 25
        return max(5, min(100, int(round(finding.impact_score * 100))))

    def _strongest_confidence(self, findings: list[InsightFinding]) -> str:
        if not findings:
            return "low"
        return max(findings, key=lambda item: CONFIDENCE_ORDER.get(item.confidence, 0)).confidence

    def _derive_account_capital(
        self,
        context: Dict[str, Any],
        closed_trades: list[Dict[str, Any]],
    ) -> float:
        account_payload = context.get("account") or {}
        for key in ("initial_balance", "current_balance", "equity"):
            value = self._to_optional_float(account_payload.get(key))
            if value and value > 0:
                return value
        for trade in closed_trades:
            value = self._to_optional_float(trade.get("equity_at_entry"))
            if value and value > 0:
                return value
        return 100000.0

    def _trade_close_key(self, trade: Dict[str, Any]) -> str:
        return str(
            trade.get("exit_time")
            or trade.get("exit_date")
            or trade.get("entry_time")
            or trade.get("entry_date")
            or ""
        )

    def _trade_weekday(self, trade: Dict[str, Any]) -> Optional[str]:
        raw = trade.get("exit_day_of_week") or trade.get("entry_day_of_week")
        if raw:
            return str(raw)
        timestamp = trade.get("exit_time") or trade.get("exit_date") or trade.get("entry_time") or trade.get("entry_date")
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).strftime("%A")
        except ValueError:
            return None

    def _short_trade_label(self, trade: Dict[str, Any], index: int) -> str:
        timestamp = trade.get("exit_date") or trade.get("exit_time") or trade.get("entry_date") or trade.get("entry_time")
        if not timestamp:
            return f"T{index + 1}"
        value = str(timestamp)
        return value[:10] if len(value) >= 10 else value

    def _max_drawdown(self, equity_curve: list[float]) -> Optional[float]:
        if len(equity_curve) < 2:
            return None
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            if peak:
                max_dd = min(max_dd, (value - peak) / peak)
        return abs(max_dd)

    def _thin_points(self, values: list[float], limit: int = 24) -> list[float]:
        if len(values) <= limit:
            return [round(float(value), 4) for value in values]
        step = (len(values) - 1) / (limit - 1)
        return [round(float(values[int(round(index * step))]), 4) for index in range(limit)]

    def _thin_labels(self, labels: list[str], limit: int) -> list[str]:
        if not labels:
            return []
        if len(labels) <= limit:
            return labels
        step = (len(labels) - 1) / (limit - 1)
        return [labels[int(round(index * step))] for index in range(limit)]

    def _direction(self, projected: float, current: float, *, lower_is_better: bool = False) -> str:
        if abs(projected - current) < 1e-9:
            return "neutral"
        improved = projected < current if lower_is_better else projected > current
        return "better" if improved else "worse"

    def _format_projection_value(self, value: float, value_type: str) -> str:
        if value_type == "currency":
            return self._format_currency(value)
        if value_type == "percent":
            return self._format_percent(value)
        return self._format_number(value)

    def _format_projection_delta(self, value: float, value_type: str) -> str:
        if value_type == "currency":
            return self._format_currency_delta(value)
        if value_type == "percent":
            return f"{value * 100:+.1f}pp"
        return f"{value:+.2f}"

    def _format_currency(self, value: float) -> str:
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.2f}"

    def _format_currency_delta(self, value: float) -> str:
        sign = "+" if value >= 0 else "-"
        return f"{sign}${abs(value):,.2f}"

    def _format_percent(self, value: float) -> str:
        return f"{value * 100:.1f}%"

    def _format_number(self, value: float) -> str:
        return f"{value:.2f}"

    def _to_float(self, value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _to_optional_float(self, value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _build_summary(
        self,
        *,
        analyses: Dict[str, Dict[str, Any]],
        summary_recommendations,
    ) -> SectionReview:
        all_wrong = []
        all_why = []
        all_right = []
        finding_lookup = {}

        for analysis in analyses.values():
            all_wrong.extend(analysis.get("wrong", []))
            all_why.extend(analysis.get("why", []))
            all_right.extend(analysis.get("right", []))

        for finding in all_wrong + all_why + all_right:
            finding_lookup[finding.id] = finding

        summary_wrong = self._filter_summary_findings(all_wrong)
        summary_why = self._filter_summary_findings(all_why)
        summary_right = self._filter_summary_findings(all_right)

        return SectionReview(
            what_is_going_wrong=rank_findings(summary_wrong, limit=3),
            why_it_is_going_wrong=rank_findings(summary_why, limit=3),
            what_is_going_right=rank_findings(summary_right, limit=3),
            what_to_do_next=rank_recommendations(summary_recommendations, limit=3, finding_lookup=finding_lookup),
        )

    def _section_from_analysis(self, analysis: Dict[str, Any], *, recommendations) -> SectionReview:
        finding_lookup = {}
        for finding in analysis.get("wrong", []) + analysis.get("why", []) + analysis.get("right", []):
            finding_lookup[finding.id] = finding
        return SectionReview(
            what_is_going_wrong=rank_findings(analysis.get("wrong", []), limit=8),
            why_it_is_going_wrong=rank_findings(analysis.get("why", []), limit=8),
            what_is_going_right=rank_findings(analysis.get("right", []), limit=8),
            what_to_do_next=rank_recommendations(recommendations, limit=6, finding_lookup=finding_lookup),
        )

    def _count_section_outputs(self, analysis: Dict[str, Any]) -> Dict[str, int]:
        return {
            "wrong": len(analysis.get("wrong", [])),
            "why": len(analysis.get("why", [])),
            "right": len(analysis.get("right", [])),
            "recommendations": len(analysis.get("recommendations", [])),
        }

    def _filter_summary_findings(self, findings):
        ranked = rank_findings(findings, limit=12)
        filtered = [finding for finding in ranked if finding.priority_score >= SUMMARY_MIN_PRIORITY]
        return filtered if filtered else ranked[:2]

    def _build_headline_summary(self, summary: SectionReview) -> list[str]:
        headline: list[str] = []
        if summary.what_is_going_wrong:
            top_wrong = summary.what_is_going_wrong[0]
            headline.append(
                f"Biggest problem right now: {top_wrong.title} (confidence {top_wrong.confidence}, sample {top_wrong.sample_size})."
            )
        if summary.what_is_going_right:
            top_right = summary.what_is_going_right[0]
            headline.append(
                f"Strongest thing to protect: {top_right.title} (confidence {top_right.confidence})."
            )
        if summary.what_to_do_next:
            headline.append(f"Best next step: {summary.what_to_do_next[0].action}")
        if not headline:
            headline.append(
                "Section analyzers are active, but there is not enough stable sample depth to rank high-confidence insights yet."
            )
        return headline

    def _build_unified_context(self, account_id: str, lookback: Optional[int]) -> Dict[str, Any]:
        trades = [trade.to_dict() for trade in self.trade_repository.get_trades_by_account(account_id=account_id)]
        if lookback is not None and lookback > 0:
            trades = trades[-lookback:]

        account_model = self.account_repository.get(account_id) if self.account_repository else None
        account = account_model.to_dict() if account_model else {}
        closed_trades = [trade for trade in trades if trade.get("is_closed")]
        missed_opportunities = [item.to_dict() for item in self.missed_opportunity_repository.list_by_account(account_id)]
        platform_sessions = [session.to_dict() for session in self.trading_platform_session_repository.list_by_account(account_id)]
        calendar_summaries = self.calendar_aggregation_engine.rebuild_for_account(account_id)
        behavior_analysis = self._build_behavior_analysis(trades, platform_sessions, missed_opportunities, lookback)
        metric_payload = self._build_metric_payload(trades, account)
        metrics_by_category, metric_errors = self._build_metric_results(metric_payload)

        return {
            "account_id": account_id,
            "account": account,
            "trades": trades,
            "closed_trades": closed_trades,
            "missed_opportunities": missed_opportunities,
            "platform_sessions": platform_sessions,
            "calendar_summaries": calendar_summaries,
            "behavior_analysis": behavior_analysis,
            "metrics_by_category": metrics_by_category,
            "metric_errors": metric_errors,
            "visible_period": self._build_visible_period(trades),
        }

    def _build_behavior_analysis(
        self,
        trades: list[Dict[str, Any]],
        platform_sessions: list[Dict[str, Any]],
        missed_opportunities: list[Dict[str, Any]],
        lookback: Optional[int],
    ) -> Dict[str, Any]:
        analysis_context = Context()
        analysis_context.set_cache("trades", trades)
        analysis_context.set_cache("trading_platform_sessions", platform_sessions)
        analysis_context.set_cache("missed_opportunities", missed_opportunities)
        return self.behavioral_analyzer.analyze(context=analysis_context, lookback=lookback)

    def _build_metric_payload(self, trades: list[Dict[str, Any]], account: Dict[str, Any]) -> Dict[str, Any]:
        closed_trades = [trade for trade in trades if trade.get("is_closed")]
        capital = self._derive_account_capital({"account": account}, closed_trades)
        daily_pnls: Dict[str, float] = defaultdict(float)
        grouped_strategies: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for trade in closed_trades:
            day_key = (
                trade.get("exit_date")
                or (str(trade.get("exit_time"))[:10] if trade.get("exit_time") else None)
                or trade.get("entry_date")
                or (str(trade.get("entry_time"))[:10] if trade.get("entry_time") else None)
            )
            if not day_key:
                continue
            net_pnl = float(trade.get("net_pnl") or 0.0)
            daily_pnls[day_key] += net_pnl
            strategy_key = str(trade.get("setup_name") or trade.get("strategy") or trade.get("strategy_tag") or "Unspecified")
            grouped_strategies[strategy_key][day_key] += self._normalize_return(net_pnl, capital=capital)

        returns = [self._normalize_return(pnl, capital=capital) for _, pnl in sorted(daily_pnls.items())]
        strategies = {
            label: [value for _, value in sorted(day_values.items())]
            for label, day_values in grouped_strategies.items()
        }

        strategy_count = len(strategies)
        return {
            "returns": returns,
            "net_pnl": [float(trade.get("net_pnl") or 0.0) for trade in closed_trades],
            "gross_pnl": [float(trade.get("gross_pnl") or 0.0) for trade in closed_trades],
            "brokerage": [float(trade.get("commission") or 0.0) + float(trade.get("fees") or 0.0) for trade in closed_trades],
            "slippage": [float(trade.get("slippage_cost") or 0.0) for trade in closed_trades],
            "swaps": [float(trade.get("swaps") or 0.0) for trade in closed_trades],
            "strategies": strategies or None,
            "capital": capital,
            "total_capital": capital,
            "target_volatility": 0.15,
            "max_drawdown_threshold": 0.25,
            "max_leverage": 3,
            "fractional_kelly": 0.5,
            "risk_budget": [1 / strategy_count] * strategy_count if strategy_count > 0 else None,
            "ruin_floor": 0.2,
            "risk_per_trade": 0.01,
        }

    def _build_metric_results(self, metric_payload: Dict[str, Any]) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, str]]]:
        metrics_by_category: Dict[str, Dict[str, Any]] = {}
        metric_errors: Dict[str, Dict[str, str]] = {}

        for category in INSIGHT_METRIC_CATEGORIES:
            execution = self.execution_engine.run(
                data=dict(metric_payload),
                registry=self.registry,
                category=category,
                phase="research",
            )
            metrics_by_category[category] = execution.all_results()
            metric_errors[category] = execution.get_errors()

        return metrics_by_category, metric_errors

    def _build_visible_period(self, trades: list[Dict[str, Any]]) -> dict[str, Optional[str]]:
        dates: list[str] = []
        for trade in trades:
            for value in (
                trade.get("entry_date"),
                trade.get("exit_date"),
                trade.get("entry_time"),
                trade.get("exit_time"),
            ):
                if isinstance(value, str) and value:
                    dates.append(value[:10])
        if not dates:
            return {"start": None, "end": None}
        dates.sort()
        return {"start": dates[0], "end": dates[-1]}

    def _normalize_return(self, pnl: float, capital: float = 100000.0) -> float:
        raw = pnl / capital if capital else 0.0
        return max(-0.999, min(raw, 10.0))
