from __future__ import annotations

from typing import Any, Dict, List, Optional

from ai.insight_scoring import build_evidence, make_finding, make_recommendation
from ai.metric_explanations import build_dashboard_metric_reviews
from ai.insights_models import DashboardChartReview, DashboardMetricReview, InsightDrilldown, InsightFinding, Recommendation


class DashboardInsightAnalyzer:
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        metrics = context.get("metrics_by_category", {})
        journal = metrics.get("journal", {})
        performance = metrics.get("performance", {})
        risk = metrics.get("risk", {})
        signals = (context.get("behavior_analysis") or {}).get("signals", {})
        sample_size = max(1, len(context.get("closed_trades", [])))

        wrong: List[InsightFinding] = []
        why: List[InsightFinding] = []
        right: List[InsightFinding] = []
        recommendations: List[Recommendation] = []

        metric_reviews = self._build_metric_reviews(journal=journal, performance=performance, risk=risk)
        chart_reviews = self._build_chart_reviews()

        max_drawdown = _to_number(risk.get("max_drawdown"))
        drawdown_finding: Optional[InsightFinding] = None
        if max_drawdown is not None and max_drawdown > 0.12:
            drawdown_finding = make_finding(
                title="Drawdown is currently above a comfortable control band",
                explanation="The portfolio drawdown level is high enough to create pressure on execution quality and sizing discipline.",
                categories=["risk", "sizing"],
                dimensions=["size", "risk_window"],
                behavior_tags=["risk_escalation"],
                sample_size=sample_size,
                impact_score=min(1.0, max_drawdown / 0.30),
                evidence=build_evidence(
                    [
                        ("Max drawdown", _format_percent(max_drawdown)),
                        ("Net Sharpe", _format_number(performance.get("net_sharpe"))),
                        ("Risk drift", _format_number(signals.get("risk_drift"))),
                    ]
                ),
                impact_description="Reducing drawdown speed protects psychological capital and recovery efficiency.",
                drilldown=InsightDrilldown(
                    view="dashboard",
                    dashboard_focus_group="Risk Metrics",
                    dashboard_focus_chart="Drawdown Curve",
                ),
            )
            wrong.append(drawdown_finding)

        profit_factor = _to_number(journal.get("profit_factor"))
        if profit_factor is not None and profit_factor < 1.0:
            why.append(
                make_finding(
                    title="Profit factor below 1 indicates losses currently outweigh gains",
                    explanation="Your aggregate gain-to-loss profile shows that losing trades are consuming more than winning trades are generating.",
                    categories=["strategy", "execution"],
                    dimensions=["setup", "market"],
                    behavior_tags=["inconsistency"],
                    sample_size=sample_size,
                    impact_score=min(1.0, 1.0 - max(0.0, profit_factor)),
                    evidence=build_evidence(
                        [
                            ("Profit factor", _format_number(profit_factor)),
                            ("Average win", _format_number(journal.get("average_win"))),
                            ("Average loss", _format_number(journal.get("average_loss"))),
                        ]
                    ),
                    impact_description="Bringing profit factor above 1.2 is usually a meaningful threshold for stability.",
                    drilldown=InsightDrilldown(
                        view="dashboard",
                        dashboard_focus_chart="Trade Outcomes",
                    ),
                )
            )

        net_sharpe = _to_number(performance.get("net_sharpe"))
        if net_sharpe is not None and net_sharpe > 1.0:
            right.append(
                make_finding(
                    title="Your core edge is still positive after adjusting for risk",
                    explanation="Your net Sharpe indicates returns are compensating reasonably for volatility taken.",
                    categories=["risk", "consistency"],
                    dimensions=["market", "session"],
                    behavior_tags=[],
                    sample_size=sample_size,
                    impact_score=min(1.0, net_sharpe / 2.0),
                    evidence=build_evidence(
                        [
                            ("Net Sharpe", _format_number(net_sharpe)),
                            ("Volatility", _format_number(risk.get("volatility"))),
                            ("Net CAGR", _format_percent(performance.get("net_cagr"))),
                        ]
                    ),
                    impact_description="Keeping this profile stable while reducing weak pockets can improve compounding consistency.",
                    drilldown=InsightDrilldown(
                        view="dashboard",
                        dashboard_focus_group="Performance Metrics",
                        dashboard_focus_chart="Performance Snapshot",
                    ),
                )
            )

        expectancy = _to_number(journal.get("expectancy"))
        if expectancy is not None and expectancy > 0:
            right.append(
                make_finding(
                    title="Expectancy is positive",
                    explanation="The current strategy stack still has positive expected value per trade.",
                    categories=["strategy", "execution"],
                    dimensions=["setup", "symbol"],
                    behavior_tags=[],
                    sample_size=sample_size,
                    impact_score=min(1.0, expectancy / (abs(expectancy) + 1.0)),
                    evidence=build_evidence(
                        [
                            ("Expectancy", _format_number(expectancy)),
                            ("Win rate", _format_percent(journal.get("win_rate"))),
                            ("Payoff ratio", _format_number(journal.get("payoff_ratio"))),
                        ]
                    ),
                    impact_description="Protecting positive expectancy is one of the highest-value behaviors in your system.",
                    drilldown=InsightDrilldown(
                        view="dashboard",
                        dashboard_focus_chart="Trade Outcomes",
                    ),
                )
            )

        if drawdown_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Add drawdown-aware risk throttling",
                    action="Cut risk per trade by 25-35% after two consecutive losses until one full-plan winner closes.",
                    why="Current drawdown pressure increases sensitivity to sizing mistakes.",
                    implementation=[
                        "Add a hard trigger at two consecutive losses.",
                        "Shift to reduced size band automatically.",
                        "Return to baseline only after one plan-compliant winner.",
                    ],
                    source_findings=[drawdown_finding],
                    expected_benefit="Lower drawdown slope and improved emotional stability during weak patches.",
                )
            )

        return {
            "wrong": wrong,
            "why": why,
            "right": right,
            "recommendations": recommendations,
            "metric_reviews": metric_reviews,
            "chart_reviews": chart_reviews,
        }

    def _build_metric_reviews(
        self,
        *,
        journal: Dict[str, Any],
        performance: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> List[DashboardMetricReview]:
        return build_dashboard_metric_reviews(
            [
                ("sharpe", performance.get("net_sharpe")),
                ("sortino", performance.get("net_sortino")),
                ("max_drawdown", risk.get("max_drawdown")),
                ("profit_factor", journal.get("profit_factor")),
                ("expectancy", journal.get("expectancy")),
                ("win_rate", journal.get("win_rate")),
                ("payoff_ratio", journal.get("payoff_ratio")),
                ("calmar", performance.get("calmar") or performance.get("net_calmar")),
                ("cagr", performance.get("net_cagr")),
            ]
        )

    def _build_chart_reviews(self) -> List[DashboardChartReview]:
        return [
            DashboardChartReview(
                chart_key="net_pnl_curve",
                label="Net P&L Curve",
                meaning="Tracks cumulative and daily profit/loss progression over time.",
                what_it_shows="Highlights growth phases, plateaus, and stress drawdown pockets.",
                important_takeaway="Monitor slope quality and drawdown depth together to avoid misleading growth impressions.",
            ),
            DashboardChartReview(
                chart_key="trade_outcomes",
                label="Trade Outcomes",
                meaning="Compares win/loss distribution and average win versus average loss balance.",
                what_it_shows="Shows whether trade quality and payoff asymmetry support positive expectancy.",
                important_takeaway="Win rate alone is insufficient if average loss size dominates average win.",
            ),
        ]


def _to_number(value: Any) -> Optional[float]:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    if output != output:
        return None
    return output


def _format_number(value: Any) -> str:
    number = _to_number(value)
    if number is None:
        return "n/a"
    return f"{number:.3f}"


def _format_percent(value: Any) -> str:
    number = _to_number(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.2f}%"
