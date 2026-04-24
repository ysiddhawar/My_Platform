from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

from ai.insight_scoring import build_evidence, make_finding, make_recommendation
from ai.insights_models import InsightDrilldown, InsightFinding, Recommendation


class CrossReferenceInsightAnalyzer:
    """
    Cross-section analyzer that links patterns across journal, dashboard,
    calendar, and missed-opportunity datasets.
    """

    def analyze(self, context: Dict[str, Any]) -> Dict[str, List[Any]]:
        trades = context.get("trades", [])
        closed = context.get("closed_trades", [])
        calendar = context.get("calendar_summaries", [])
        missed = context.get("missed_opportunities", [])
        sample_size = max(1, len(closed))

        wrong: List[InsightFinding] = []
        why: List[InsightFinding] = []
        right: List[InsightFinding] = []
        recommendations: List[Recommendation] = []

        setup_symbol_finding = self._analyze_setup_symbol_split(closed, sample_size)
        if setup_symbol_finding is not None:
            wrong.append(setup_symbol_finding)

        weekday_size_finding = self._analyze_weekday_size_drift(closed, sample_size)
        if weekday_size_finding is not None:
            wrong.append(weekday_size_finding)

        session_time_finding = self._analyze_session_time_vs_pnl(calendar, sample_size)
        if session_time_finding is not None:
            why.append(session_time_finding)

        missed_setup_finding = self._analyze_missed_vs_taken_setup_gap(closed, missed, sample_size)
        if missed_setup_finding is not None:
            why.append(missed_setup_finding)

        best_edge_finding = self._analyze_best_edge_pair(closed, sample_size)
        if best_edge_finding is not None:
            right.append(best_edge_finding)

        if setup_symbol_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Concentrate risk on validated setup-symbol edges",
                    action="Reduce exposure to weak setup-symbol pairs and shift that allocation toward your strongest pair.",
                    why="Cross-referencing setup and symbol performance shows a meaningful edge gap.",
                    implementation=[
                        "Identify the weakest setup-symbol pair from the evidence block and cap risk by 30%.",
                        "Increase focus on the strongest pair only when checklist and context match.",
                        "Re-evaluate pair expectancy weekly and keep a minimum sample gate of 10 trades.",
                    ],
                    source_findings=[setup_symbol_finding],
                    expected_benefit="Improves capital efficiency by allocating risk toward proven edge combinations.",
                )
            )

        if weekday_size_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Apply weekday-aware position sizing",
                    action="Reduce risk on the highest-risk negative weekday and restore baseline on stable weekdays.",
                    why="Sizing and day-of-week are currently interacting in a way that amplifies losses.",
                    implementation=[
                        "Tag your highest-risk weekday from the evidence section.",
                        "Cut base size by 20-30% on that day for four weeks.",
                        "Measure expectancy change by weekday before normalizing size.",
                    ],
                    source_findings=[weekday_size_finding],
                    expected_benefit="Lowers avoidable downside concentration while preserving strong-session opportunity.",
                )
            )

        if missed_setup_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Close the missed-vs-taken setup execution gap",
                    action="Create one execution trigger checklist for the most-missed setup and enforce it in real time.",
                    why="Cross-reference of missed and taken setups shows execution leakage where edge should be captured.",
                    implementation=[
                        "Select the top missed setup from evidence and define 3 mandatory trigger conditions.",
                        "When conditions are met, require execute-or-document-skip in journal notes.",
                        "Review missed profitable instances each week and refine one rule only.",
                    ],
                    source_findings=[missed_setup_finding],
                    expected_benefit="Turns recognized opportunities into realized trades with better consistency.",
                )
            )

        return {
            "wrong": wrong,
            "why": why,
            "right": right,
            "recommendations": recommendations,
        }

    def _analyze_setup_symbol_split(self, closed: List[Dict[str, Any]], sample_size: int) -> Optional[InsightFinding]:
        pair_stats: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        for trade in closed:
            setup = str(trade.get("setup_name") or trade.get("strategy") or trade.get("strategy_tag") or "Unspecified")
            symbol = str(trade.get("symbol") or "Unknown")
            pair_stats[(setup, symbol)].append(float(trade.get("net_pnl") or 0.0))

        qualified = {pair: values for pair, values in pair_stats.items() if len(values) >= 5}
        if len(qualified) < 2:
            return None

        pair_avg = {pair: sum(values) / len(values) for pair, values in qualified.items()}
        worst_pair = min(pair_avg, key=pair_avg.get)
        best_pair = max(pair_avg, key=pair_avg.get)

        if pair_avg[worst_pair] >= 0:
            return None

        impact = min(1.0, abs(pair_avg[worst_pair] - pair_avg[best_pair]) / max(1.0, abs(pair_avg[best_pair]) + 1.0))
        return make_finding(
            title="The same setup is not working equally well across symbols",
            explanation="The same setup is not performing equally across symbols, which suggests edge quality is symbol-dependent.",
            categories=["strategy", "execution"],
            dimensions=["setup", "symbol", "market"],
            behavior_tags=["inconsistency"],
            sample_size=sample_size,
            impact_score=impact,
            evidence=build_evidence(
                [
                    ("Weakest setup-symbol pair", f"{worst_pair[0]} on {worst_pair[1]}"),
                    ("Weak pair average P&L", f"{pair_avg[worst_pair]:.2f}"),
                    ("Strongest setup-symbol pair", f"{best_pair[0]} on {best_pair[1]}"),
                    ("Strong pair average P&L", f"{pair_avg[best_pair]:.2f}"),
                ]
            ),
            impact_description="Treating all symbols the same for one setup can hide and amplify edge decay.",
            drilldown=InsightDrilldown(
                view="dashboard",
                dashboard_filters_patch={"strategyFilter": worst_pair[0], "symbolFilter": worst_pair[1]},
                dashboard_focus_group="Performance Metrics",
                dashboard_focus_chart="Trade Outcomes",
            ),
        )

    def _analyze_weekday_size_drift(self, closed: List[Dict[str, Any]], sample_size: int) -> Optional[InsightFinding]:
        weekday_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"risk_sum": 0.0, "pnl_sum": 0.0, "count": 0.0})
        for trade in closed:
            weekday = str(trade.get("entry_day_of_week") or "Unknown")
            risk = float(trade.get("risk_amount") or 0.0)
            pnl = float(trade.get("net_pnl") or 0.0)
            weekday_stats[weekday]["risk_sum"] += max(0.0, risk)
            weekday_stats[weekday]["pnl_sum"] += pnl
            weekday_stats[weekday]["count"] += 1

        qualified = {day: stats for day, stats in weekday_stats.items() if stats["count"] >= 3}
        if len(qualified) < 2:
            return None

        avg_risk = {day: stats["risk_sum"] / max(1.0, stats["count"]) for day, stats in qualified.items()}
        avg_pnl = {day: stats["pnl_sum"] / max(1.0, stats["count"]) for day, stats in qualified.items()}

        highest_risk_day = max(avg_risk, key=avg_risk.get)
        if avg_pnl[highest_risk_day] >= 0:
            return None

        overall_avg_risk = sum(avg_risk.values()) / len(avg_risk)
        impact = min(1.0, abs(avg_pnl[highest_risk_day]) / max(1.0, abs(min(avg_pnl.values())) + 1.0))
        return make_finding(
            title="Highest-risk weekday is producing negative average returns",
            explanation="Risk allocation is currently largest on a weekday where average outcome is negative.",
            categories=["risk", "sizing", "discipline"],
            dimensions=["day", "size", "frequency"],
            behavior_tags=["risk_escalation", "inconsistency"],
            sample_size=sample_size,
            impact_score=impact,
            evidence=build_evidence(
                [
                    ("Highest-risk weekday", highest_risk_day),
                    ("Avg risk on that day", f"{avg_risk[highest_risk_day]:.2f}", f"overall {overall_avg_risk:.2f}"),
                    ("Avg P&L on that day", f"{avg_pnl[highest_risk_day]:.2f}"),
                ]
            ),
            impact_description="This mismatch increases downside concentration exactly where edge is weaker.",
            drilldown=InsightDrilldown(
                view="dashboard",
                dashboard_filters_patch={"dayFilter": highest_risk_day},
                dashboard_focus_chart="Trade Outcomes",
            ),
        )

    def _analyze_missed_vs_taken_setup_gap(
        self,
        closed: List[Dict[str, Any]],
        missed: List[Dict[str, Any]],
        sample_size: int,
    ) -> Optional[InsightFinding]:
        if not missed or not closed:
            return None

        missed_by_setup = Counter(str(item.get("strategy_name") or "Unspecified") for item in missed)
        taken_by_setup = Counter(
            str(trade.get("setup_name") or trade.get("strategy") or trade.get("strategy_tag") or "Unspecified")
            for trade in closed
        )

        top_missed_setup, top_missed_count = missed_by_setup.most_common(1)[0]
        taken_count = taken_by_setup.get(top_missed_setup, 0)
        if top_missed_count < 4:
            return None

        missed_to_taken = top_missed_count / max(1, taken_count)
        if missed_to_taken < 1.0:
            return None
        impact = min(1.0, missed_to_taken / 2.0)
        return make_finding(
            title="Missed opportunities are concentrated in a specific setup",
            explanation="One setup is being observed often but executed less consistently, indicating a capture gap.",
            categories=["execution", "strategy", "consistency"],
            dimensions=["setup", "session", "symbol"],
            behavior_tags=["hesitation"],
            sample_size=sample_size,
            impact_score=impact,
            evidence=build_evidence(
                [
                    ("Top missed setup", f"{top_missed_setup} ({top_missed_count})"),
                    ("Taken trades in same setup", str(taken_count)),
                    ("Missed/taken ratio", f"{missed_to_taken:.2f}"),
                ]
            ),
            impact_description="Closing this gap can increase realized edge without forcing higher trade volume.",
            drilldown=InsightDrilldown(
                view="missed-opportunities",
                missed_opportunity_search_text=top_missed_setup,
            ),
        )

    def _analyze_session_time_vs_pnl(self, calendar: List[Dict[str, Any]], sample_size: int) -> Optional[InsightFinding]:
        if len(calendar) < 8:
            return None

        active_days = [row for row in calendar if float(row.get("trade_count") or 0.0) > 0]
        if len(active_days) < 6:
            return None

        times = [float(row.get("total_platform_time_minutes") or 0.0) for row in active_days]
        pivot = median(times)
        high_time = [row for row in active_days if float(row.get("total_platform_time_minutes") or 0.0) >= pivot]
        low_time = [row for row in active_days if float(row.get("total_platform_time_minutes") or 0.0) < pivot]
        if not high_time or not low_time:
            return None

        high_avg = sum(float(row.get("pnl") or 0.0) for row in high_time) / len(high_time)
        low_avg = sum(float(row.get("pnl") or 0.0) for row in low_time) / len(low_time)
        if high_avg >= low_avg:
            return None
        worst_high_time_day = min(
            high_time,
            key=lambda row: float(row.get("pnl") or 0.0),
        )
        representative_day = str(worst_high_time_day.get("day") or "")

        impact = min(1.0, abs(high_avg - low_avg) / max(1.0, abs(low_avg) + 1.0))
        return make_finding(
            title="Longer session-time days are underperforming shorter session-time days",
            explanation="Calendar and session data together suggest decision quality may degrade as session duration extends.",
            categories=["discipline", "consistency", "execution"],
            dimensions=["session", "time", "frequency"],
            behavior_tags=["inconsistency"],
            sample_size=sample_size,
            impact_score=impact,
            evidence=build_evidence(
                [
                    ("Median platform minutes", f"{pivot:.0f}"),
                    ("Avg P&L high-time days", f"{high_avg:.2f}"),
                    ("Avg P&L low-time days", f"{low_avg:.2f}"),
                    ("Representative high-time day", representative_day or "n/a"),
                ]
            ),
            impact_description="Session-time control can improve focus quality and reduce fatigue-driven trade degradation.",
            drilldown=_calendar_day_drilldown(representative_day) if representative_day else None,
        )

    def _analyze_best_edge_pair(self, closed: List[Dict[str, Any]], sample_size: int) -> Optional[InsightFinding]:
        pair_stats: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        for trade in closed:
            setup = str(trade.get("setup_name") or trade.get("strategy") or trade.get("strategy_tag") or "Unspecified")
            symbol = str(trade.get("symbol") or "Unknown")
            pair_stats[(setup, symbol)].append(float(trade.get("net_pnl") or 0.0))

        qualified = {pair: values for pair, values in pair_stats.items() if len(values) >= 5}
        if not qualified:
            return None

        pair_avg = {pair: sum(values) / len(values) for pair, values in qualified.items()}
        best_pair = max(pair_avg, key=pair_avg.get)
        if pair_avg[best_pair] <= 0:
            return None

        impact = min(1.0, pair_avg[best_pair] / max(1.0, abs(pair_avg[best_pair]) + 1.0))
        return make_finding(
            title="A repeatable setup-symbol edge is visible",
            explanation="Cross-referencing setup and symbol reveals one pair with consistently stronger average outcomes.",
            categories=["strategy", "consistency"],
            dimensions=["setup", "symbol", "market"],
            behavior_tags=["consistency"],
            sample_size=sample_size,
            impact_score=impact,
            evidence=build_evidence(
                [
                    ("Best setup-symbol pair", f"{best_pair[0]} on {best_pair[1]}"),
                    ("Average P&L for pair", f"{pair_avg[best_pair]:.2f}"),
                    ("Sample count", str(len(qualified[best_pair]))),
                ]
            ),
            impact_description="Leaning into proven pair-level edges can improve reward efficiency with less noise.",
            drilldown=InsightDrilldown(
                view="dashboard",
                dashboard_filters_patch={"strategyFilter": best_pair[0], "symbolFilter": best_pair[1]},
                dashboard_focus_group="Performance Metrics",
                dashboard_focus_chart="Trade Outcomes",
            ),
        )


def _calendar_day_drilldown(day: str) -> InsightDrilldown | None:
    try:
        parsed = datetime.fromisoformat(day)
    except ValueError:
        return None
    return InsightDrilldown(
        view="calendar",
        selected_day=day,
        calendar_visible_month=parsed.month - 1,
        calendar_visible_year=parsed.year,
    )
