from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from ai.insight_scoring import build_evidence, make_finding, make_recommendation
from ai.insights_models import InsightDrilldown, InsightFinding, Recommendation


class CalendarInsightAnalyzer:
    def analyze(self, context: Dict[str, Any]) -> Dict[str, List[Any]]:
        calendar = context.get("calendar_summaries", [])
        sessions = context.get("platform_sessions", [])
        sample_size = max(1, len(calendar))

        wrong: List[InsightFinding] = []
        why: List[InsightFinding] = []
        right: List[InsightFinding] = []
        recommendations: List[Recommendation] = []

        weekday_stats = self._weekday_stats(calendar)
        if weekday_stats["worst_day"] is not None and weekday_stats["worst_pnl"] < 0:
            worst_day = weekday_stats["worst_day"]
            worst_day_finding = make_finding(
                title=f"{worst_day} is a recurring weak day",
                explanation="Calendar day-level P&L shows one weekday repeatedly underperforming others.",
                categories=["consistency", "execution"],
                dimensions=["day", "time", "session"],
                behavior_tags=["inconsistency"],
                sample_size=sample_size,
                impact_score=min(1.0, abs(weekday_stats["worst_pnl"]) / max(1.0, abs(weekday_stats["best_pnl"]))),
                evidence=build_evidence(
                    [
                        ("Worst weekday avg P&L", f"{worst_day}: {weekday_stats['worst_pnl']:.2f}"),
                        ("Best weekday avg P&L", f"{weekday_stats['best_day']}: {weekday_stats['best_pnl']:.2f}"),
                        ("Active weekday count", str(weekday_stats["active_days"])),
                        ("Representative weak day", weekday_stats["worst_day_example"] or "n/a"),
                    ]
                ),
                impact_description="Filtering weak weekday windows can reduce avoidable loss clusters.",
                drilldown=_calendar_day_drilldown(weekday_stats["worst_day_example"]),
            )
            wrong.append(worst_day_finding)

            recommendations.append(
                make_recommendation(
                    title="Apply weekday quality filter",
                    action=f"Trade smaller or skip low-conviction setups on {worst_day} for the next 4 weeks.",
                    why="Calendar performance suggests that day has lower edge realization.",
                    implementation=[
                        f"On {worst_day}, only trade top-conviction setups.",
                        "Reduce risk band by 20% on that day.",
                        "Compare weekly expectancy before/after this filter.",
                    ],
                    source_findings=[worst_day_finding],
                    expected_benefit="Reduced weekly variance and improved day-level consistency.",
                )
            )

        if sessions:
            avg_minutes = self._average_session_minutes(sessions)
            longest_session_day = self._representative_long_session_day(sessions)
            if len(sessions) >= 8 and avg_minutes >= 120:
                why.append(
                    make_finding(
                        title="Long session duration is likely affecting execution quality",
                        explanation="Your session profile is long enough that fatigue and lower-quality decision-making become more likely.",
                        categories=["discipline", "consistency"],
                        dimensions=["session", "time"],
                        behavior_tags=["inconsistency"],
                        sample_size=max(1, len(sessions)),
                        impact_score=min(1.0, avg_minutes / 480.0),
                        evidence=build_evidence(
                            [
                                ("Average session minutes", f"{avg_minutes:.1f}"),
                                ("Session count", str(len(sessions))),
                                ("Representative long-session day", longest_session_day or "n/a"),
                            ]
                        ),
                        impact_description="Session-time control can improve focus and reduce degraded late-session decisions.",
                        drilldown=_calendar_day_drilldown(longest_session_day),
                    )
                )

        if weekday_stats["best_day"] is not None and weekday_stats["best_pnl"] > 0:
            right.append(
                make_finding(
                    title=f"{weekday_stats['best_day']} is a current strength day",
                    explanation="One weekday is consistently producing better average daily outcomes.",
                    categories=["strategy", "consistency"],
                    dimensions=["day", "session"],
                    behavior_tags=["consistency"],
                    sample_size=sample_size,
                    impact_score=min(1.0, weekday_stats["best_pnl"] / max(1.0, abs(weekday_stats["worst_pnl"]))),
                    evidence=build_evidence(
                        [
                            ("Best weekday avg P&L", f"{weekday_stats['best_day']}: {weekday_stats['best_pnl']:.2f}"),
                            ("Worst weekday avg P&L", f"{weekday_stats['worst_day']}: {weekday_stats['worst_pnl']:.2f}" if weekday_stats["worst_day"] else "n/a"),
                            ("Representative strong day", weekday_stats["best_day_example"] or "n/a"),
                        ]
                    ),
                    impact_description="Leaning into stronger weekday windows can improve quality-adjusted allocation.",
                    drilldown=_calendar_day_drilldown(weekday_stats["best_day_example"]),
                )
            )

        return {
            "wrong": wrong,
            "why": why,
            "right": right,
            "recommendations": recommendations,
        }

    def _weekday_stats(self, calendar: List[Dict[str, Any]]) -> Dict[str, Any]:
        buckets: Dict[str, List[float]] = defaultdict(list)
        best_day_example: Dict[str, tuple[str, float]] = {}
        worst_day_example: Dict[str, tuple[str, float]] = {}
        for item in calendar:
            day_value = item.get("day")
            if not day_value:
                continue
            try:
                dt = datetime.fromisoformat(str(day_value))
            except ValueError:
                continue
            label = dt.strftime("%A")
            pnl = float(item.get("pnl") or 0.0)
            buckets[label].append(pnl)
            current_best = best_day_example.get(label)
            current_worst = worst_day_example.get(label)
            if current_best is None or pnl > current_best[1]:
                best_day_example[label] = (str(day_value), pnl)
            if current_worst is None or pnl < current_worst[1]:
                worst_day_example[label] = (str(day_value), pnl)

        if not buckets:
            return {
                "best_day": None,
                "best_pnl": 0.0,
                "best_day_example": None,
                "worst_day": None,
                "worst_pnl": 0.0,
                "worst_day_example": None,
                "active_days": 0,
            }

        averages = {key: sum(values) / len(values) for key, values in buckets.items()}
        best_day = max(averages, key=averages.get)
        worst_day = min(averages, key=averages.get)
        return {
            "best_day": best_day,
            "best_pnl": averages[best_day],
            "best_day_example": best_day_example.get(best_day, (None, 0.0))[0],
            "worst_day": worst_day,
            "worst_pnl": averages[worst_day],
            "worst_day_example": worst_day_example.get(worst_day, (None, 0.0))[0],
            "active_days": len(averages),
        }

    def _average_session_minutes(self, sessions: List[Dict[str, Any]]) -> float:
        values = []
        for session in sessions:
            minutes = session.get("duration_minutes")
            if minutes is None:
                minutes = session.get("minutes_within_day")
            try:
                values.append(float(minutes))
            except (TypeError, ValueError):
                continue
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _representative_long_session_day(self, sessions: List[Dict[str, Any]]) -> str | None:
        best_day = None
        best_minutes = -1.0
        for session in sessions:
            day = _extract_session_day(session)
            if not day:
                continue
            minutes = session.get("duration_minutes")
            if minutes is None:
                minutes = session.get("minutes_within_day")
            try:
                parsed_minutes = float(minutes)
            except (TypeError, ValueError):
                continue
            if parsed_minutes > best_minutes:
                best_minutes = parsed_minutes
                best_day = day
        return best_day


def _calendar_day_drilldown(day: str | None) -> InsightDrilldown | None:
    if not day:
        return None
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


def _extract_session_day(session: Dict[str, Any]) -> str | None:
    candidates = [
        session.get("day"),
        session.get("local_date"),
        session.get("session_day"),
        session.get("trade_day"),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    for field in ("started_at", "start_time", "session_start"):
        value = session.get(field)
        if value:
            return str(value)[:10]
    return None
