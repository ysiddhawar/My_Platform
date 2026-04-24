from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from ai.insight_scoring import build_evidence, make_finding, make_recommendation
from ai.insights_models import InsightDrilldown, InsightFinding, Recommendation


class JournalInsightAnalyzer:
    def analyze(self, context: Dict[str, Any]) -> Dict[str, List[Any]]:
        trades = context.get("trades", [])
        closed = context.get("closed_trades", [])
        signals = (context.get("behavior_analysis") or {}).get("signals", {})
        sample_size = max(1, len(closed))

        wrong: List[InsightFinding] = []
        why: List[InsightFinding] = []
        right: List[InsightFinding] = []
        recommendations: List[Recommendation] = []

        avg_trades = self._average_trades_per_active_day(trades)
        overtrading_finding = None
        busiest_day = self._busiest_day(trades)
        if avg_trades > 5:
            overtrading_finding = make_finding(
                title="You are trading too often for your current level of control",
                explanation="You are taking many trades per active day, which usually increases low-quality executions.",
                categories=["discipline", "frequency"],
                dimensions=["frequency", "day"],
                behavior_tags=["overtrading", "inconsistency"],
                sample_size=sample_size,
                impact_score=min(1.0, (avg_trades - 3.0) / 7.0),
                evidence=build_evidence(
                    [
                        ("Average trades per active day", f"{avg_trades:.2f}"),
                        ("Closed trades in sample", str(len(closed))),
                        ("Busiest day", f"{busiest_day[0]} ({busiest_day[1]} trades)" if busiest_day else "n/a"),
                    ]
                ),
                impact_description="Reducing excess trade count often improves expectancy by cutting low-conviction entries.",
                drilldown=_calendar_day_drilldown(busiest_day[0]) if busiest_day else None,
            )
            wrong.append(overtrading_finding)

        loss_streak = int(_to_number(signals.get("loss_streak_length")) or 0)
        streak_finding = None
        streak_trade_id = self._last_loss_streak_trade_id(closed)
        if loss_streak >= 3:
            streak_finding = make_finding(
                title="Losses are clustering instead of staying random",
                explanation="A long loss streak often points to process drift, not just variance.",
                categories=["execution", "discipline"],
                dimensions=["session", "psychology"],
                behavior_tags=["discipline_break", "inconsistency"],
                sample_size=sample_size,
                impact_score=min(1.0, loss_streak / 8.0),
                evidence=build_evidence(
                    [
                        ("Longest loss streak", str(loss_streak)),
                        ("Violation frequency", _format_percent(signals.get("violation_frequency"))),
                    ]
                ),
                impact_description="Stabilizing behavior during streaks limits cascading drawdown damage.",
                drilldown=InsightDrilldown(view="journal", journal_search_text="", selected_trade_id=streak_trade_id) if streak_trade_id else None,
            )
            wrong.append(streak_finding)

        strategy_switch_frequency = _to_number(signals.get("strategy_switch_frequency"))
        if strategy_switch_frequency is not None and strategy_switch_frequency > 0.20:
            why.append(
                make_finding(
                    title="Frequent strategy switching is likely degrading consistency",
                    explanation="Switching setups too often can reduce pattern familiarity and execution quality.",
                    categories=["strategy", "discipline"],
                    dimensions=["setup", "market"],
                    behavior_tags=["fomo", "inconsistency"],
                    sample_size=sample_size,
                    impact_score=min(1.0, strategy_switch_frequency),
                    evidence=build_evidence(
                        [
                            ("Strategy switch frequency", _format_percent(strategy_switch_frequency)),
                            ("Checklist compliance", _format_percent(signals.get("checklist_compliance_rate"))),
                        ]
                    ),
                    impact_description="Lower setup churn often improves trade quality and confidence.",
                )
            )

        early_exit_rate = _to_number(signals.get("early_exit_rate"))
        if early_exit_rate is not None and early_exit_rate > 0.25:
            early_exit_trade = self._first_early_exit_trade_id(closed)
            why.append(
                make_finding(
                    title="Early exits are likely reducing reward capture",
                    explanation="Closing winners too early cuts average reward and weakens payoff profile.",
                    categories=["execution", "psychology"],
                    dimensions=["time", "session"],
                    behavior_tags=["hesitation"],
                    sample_size=sample_size,
                    impact_score=min(1.0, early_exit_rate),
                    evidence=build_evidence(
                        [
                            ("Early exit rate", _format_percent(early_exit_rate)),
                            ("Closed trades", str(len(closed))),
                        ]
                    ),
                    impact_description="Holding to planned exits can improve average win size and expectancy.",
                    drilldown=InsightDrilldown(
                        view="dashboard",
                        dashboard_filters_patch={"closedEarlyFilter": "yes"},
                        dashboard_focus_group="Performance Metrics",
                        dashboard_focus_chart="Trade Outcomes",
                        selected_trade_id=early_exit_trade,
                    ),
                )
            )

        checklist_compliance = _to_number(signals.get("checklist_compliance_rate"))
        if checklist_compliance is not None and checklist_compliance >= 0.70:
            right.append(
                make_finding(
                    title="Checklist adherence is a clear discipline strength",
                    explanation="You are following checklist requirements at a strong rate, which supports execution stability.",
                    categories=["discipline", "execution"],
                    dimensions=["setup", "session"],
                    behavior_tags=["consistency"],
                    sample_size=sample_size,
                    impact_score=min(1.0, checklist_compliance),
                    evidence=build_evidence(
                        [
                            ("Checklist compliance", _format_percent(checklist_compliance)),
                            ("Notes density", _format_percent(signals.get("notes_density"))),
                        ]
                    ),
                    impact_description="Preserving this habit gives your strategy a repeatable process edge.",
                )
            )

        if overtrading_finding is not None:
            cap = max(3, int(round(avg_trades * 0.6)))
            recommendations.append(
                make_recommendation(
                    title="Add a hard daily trade cap",
                    action=f"Limit to {cap} trades per active day for the next 20 trading days.",
                    why="This directly addresses overtrading pressure seen in your journal behavior.",
                    implementation=[
                        f"Stop opening new positions after {cap} trades in a day.",
                        "Log one-line reason for every skipped extra setup.",
                        "Review weekly expectancy before and after applying the cap.",
                    ],
                    source_findings=[overtrading_finding],
                    expected_benefit="Cleaner setup selection and improved consistency of outcomes.",
                )
            )

        if streak_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Use a loss-streak reset rule",
                    action="After 3 consecutive losses, pause entries and run a short process review before trading again.",
                    why="This reduces the chance of emotional continuation mistakes.",
                    implementation=[
                        "Pause entries for one full setup cycle.",
                        "Review the last 3 losses against checklist and setup validity.",
                        "Resume with reduced risk on first trade after reset.",
                    ],
                    source_findings=[streak_finding],
                    expected_benefit="Lower probability of cascading losses.",
                )
            )

        return {
            "wrong": wrong,
            "why": why,
            "right": right,
            "recommendations": recommendations,
        }

    def _average_trades_per_active_day(self, trades: List[Dict[str, Any]]) -> float:
        by_day: Dict[str, int] = defaultdict(int)
        for trade in trades:
            day = (
                trade.get("entry_date")
                or (str(trade.get("entry_time"))[:10] if trade.get("entry_time") else None)
                or trade.get("exit_date")
            )
            if not day:
                continue
            by_day[str(day)] += 1
        if not by_day:
            return 0.0
        return sum(by_day.values()) / len(by_day)

    def _busiest_day(self, trades: List[Dict[str, Any]]) -> tuple[str, int] | None:
        by_day: Dict[str, int] = defaultdict(int)
        for trade in trades:
            day = (
                trade.get("entry_date")
                or (str(trade.get("entry_time"))[:10] if trade.get("entry_time") else None)
                or trade.get("exit_date")
            )
            if not day:
                continue
            by_day[str(day)] += 1
        if not by_day:
            return None
        return max(by_day.items(), key=lambda item: (item[1], item[0]))

    def _last_loss_streak_trade_id(self, closed: List[Dict[str, Any]]) -> str | None:
        ordered = sorted(
            closed,
            key=lambda trade: str(
                trade.get("exit_time")
                or trade.get("exit_date")
                or trade.get("entry_time")
                or trade.get("entry_date")
                or ""
            ),
        )
        current_streak: List[Dict[str, Any]] = []
        best_streak: List[Dict[str, Any]] = []
        for trade in ordered:
            pnl = float(trade.get("net_pnl") or 0.0)
            if pnl < 0:
                current_streak.append(trade)
                if len(current_streak) >= len(best_streak):
                    best_streak = list(current_streak)
            else:
                current_streak = []
        if not best_streak:
            return None
        return str(best_streak[-1].get("trade_id") or "") or None

    def _first_early_exit_trade_id(self, closed: List[Dict[str, Any]]) -> str | None:
        for trade in closed:
            if trade.get("closed_before_plan") or str(trade.get("close_classification") or "").lower() == "early":
                trade_id = str(trade.get("trade_id") or "")
                if trade_id:
                    return trade_id
        return None


def _to_number(value: Any) -> float | None:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    if output != output:
        return None
    return output


def _format_percent(value: Any) -> str:
    number = _to_number(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.2f}%"


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
