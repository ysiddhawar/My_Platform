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
from ai.insights_models import AIInsightsMetadata, AIInsightsResponse, DashboardDetailedReview, SectionReview


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
            detailed_review=detailed_review,
            metadata=metadata,
        )

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

        closed_trades = [trade for trade in trades if trade.get("is_closed")]
        missed_opportunities = [item.to_dict() for item in self.missed_opportunity_repository.list_by_account(account_id)]
        platform_sessions = [session.to_dict() for session in self.trading_platform_session_repository.list_by_account(account_id)]
        calendar_summaries = self.calendar_aggregation_engine.rebuild_for_account(account_id)
        behavior_analysis = self._build_behavior_analysis(trades, platform_sessions, missed_opportunities, lookback)
        metric_payload = self._build_metric_payload(trades)
        metrics_by_category, metric_errors = self._build_metric_results(metric_payload)

        return {
            "account_id": account_id,
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

    def _build_metric_payload(self, trades: list[Dict[str, Any]]) -> Dict[str, Any]:
        closed_trades = [trade for trade in trades if trade.get("is_closed")]
        daily_pnls: Dict[str, float] = defaultdict(float)
        grouped_strategies: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for trade in closed_trades:
            day_key = (
                trade.get("exit_date")
                or trade.get("entry_date")
                or (str(trade.get("exit_time"))[:10] if trade.get("exit_time") else None)
                or (str(trade.get("entry_time"))[:10] if trade.get("entry_time") else None)
            )
            if not day_key:
                continue
            net_pnl = float(trade.get("net_pnl") or 0.0)
            daily_pnls[day_key] += net_pnl
            strategy_key = str(trade.get("setup_name") or trade.get("strategy") or trade.get("strategy_tag") or "Unspecified")
            grouped_strategies[strategy_key][day_key] += self._normalize_return(net_pnl)

        returns = [self._normalize_return(pnl) for _, pnl in sorted(daily_pnls.items())]
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
            "capital": 100000,
            "total_capital": 100000,
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
