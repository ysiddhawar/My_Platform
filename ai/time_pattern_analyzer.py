from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.trade_outcome import classify_trade_outcome
from models.ai_diagnosis import DiagnosticFinding


class TimePatternAnalyzer:
    """
    Extracts time-based trading patterns from executed trades and platform sessions.

    The goal is not to enumerate every possible insight up front. It creates a
    broad, structured layer of time/day/session features that later diagnosis
    stages can interpret and extend.
    """

    def analyze(
        self,
        trades: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not trades and not sessions:
            return self._empty_payload()

        hour_stats = self._aggregate_trade_hours(trades)
        day_stats = self._aggregate_trade_days(trades)
        strategy_hour_stats = self._aggregate_strategy_hours(trades)
        session_daily_totals = self._aggregate_session_daily_minutes(sessions)
        session_hour_coverage = self._aggregate_session_hour_coverage(sessions)

        strongest_hour = self._pick_extreme(hour_stats, highest=True)
        weakest_hour = self._pick_extreme(hour_stats, highest=False)
        strongest_day = self._pick_extreme(day_stats, highest=True)
        weakest_day = self._pick_extreme(day_stats, highest=False)
        strongest_strategy_window = self._pick_best_strategy_window(strategy_hour_stats)
        coverage_gap = self._detect_underused_profitable_window(
            strongest_hour,
            session_hour_coverage,
        )
        low_time_day = self._detect_low_time_vs_baseline(session_daily_totals)

        findings: List[DiagnosticFinding] = []
        strengths: List[DiagnosticFinding] = []

        if strongest_hour and strongest_hour["average_net_pnl"] > 0 and strongest_hour["trade_count"] >= 2:
            strengths.append(
                DiagnosticFinding(
                    category="time",
                    title="Strong trading hour identified",
                    description=(
                        f"Hour {strongest_hour['label']} is a consistently strong window based on recent executed trades."
                    ),
                    severity="info",
                    metric_reference="strongest_hour",
                    value=strongest_hour["average_net_pnl"],
                    metadata=strongest_hour,
                )
            )

        if weakest_hour and weakest_hour["average_net_pnl"] < 0 and weakest_hour["trade_count"] >= 2:
            findings.append(
                DiagnosticFinding(
                    category="time",
                    title="Weak trading hour detected",
                    description=(
                        f"Hour {weakest_hour['label']} is underperforming relative to other active hours and may need tighter filters."
                    ),
                    severity="medium",
                    metric_reference="weakest_hour",
                    value=weakest_hour["average_net_pnl"],
                    threshold=0.0,
                    metadata=weakest_hour,
                )
            )

        if strongest_day and strongest_day["average_net_pnl"] > 0 and strongest_day["trade_count"] >= 2:
            strengths.append(
                DiagnosticFinding(
                    category="time",
                    title="Strong weekday edge present",
                    description=(
                        f"{strongest_day['label']} is producing the strongest average result in the recent sample."
                    ),
                    severity="info",
                    metric_reference="strongest_day",
                    value=strongest_day["average_net_pnl"],
                    metadata=strongest_day,
                )
            )

        if weakest_day and weakest_day["average_net_pnl"] < 0 and weakest_day["trade_count"] >= 2:
            findings.append(
                DiagnosticFinding(
                    category="time",
                    title="Weak weekday cluster detected",
                    description=(
                        f"{weakest_day['label']} is the weakest weekday in the recent sample, which suggests a repeatable calendar drag."
                    ),
                    severity="medium",
                    metric_reference="weakest_day",
                    value=weakest_day["average_net_pnl"],
                    threshold=0.0,
                    metadata=weakest_day,
                )
            )

        if strongest_strategy_window:
            strengths.append(
                DiagnosticFinding(
                    category="time",
                    title="Strategy timing edge visible",
                    description=(
                        f"{strongest_strategy_window['strategy_tag']} performs best around {strongest_strategy_window['label']} in the current sample."
                    ),
                    severity="info",
                    metric_reference="strategy_hour_edge",
                    value=strongest_strategy_window["average_net_pnl"],
                    metadata=strongest_strategy_window,
                )
            )

        if coverage_gap is not None:
            findings.append(
                DiagnosticFinding(
                    category="time",
                    title="High-performing window underused",
                    description=(
                        f"The strongest trading hour ({coverage_gap['label']}) has lighter platform-session coverage than the user's broader activity pattern."
                    ),
                    severity="medium",
                    metric_reference="underused_profitable_window",
                    value=coverage_gap["coverage_ratio"],
                    threshold=coverage_gap["baseline_coverage_ratio"],
                    metadata=coverage_gap,
                )
            )

        if low_time_day is not None:
            findings.append(
                DiagnosticFinding(
                    category="time",
                    title="Platform time below baseline",
                    description=(
                        "Recent platform time fell materially below the trader's own daily baseline, which can indicate missed screen time during usable sessions."
                    ),
                    severity="low",
                    metric_reference="platform_time_baseline_gap",
                    value=low_time_day["recent_minutes"],
                    threshold=low_time_day["baseline_minutes"],
                    metadata=low_time_day,
                )
            )

        return {
            "features": {
                "hourly_trade_stats": hour_stats,
                "weekday_trade_stats": day_stats,
                "strategy_hour_stats": strategy_hour_stats,
                "session_daily_totals": session_daily_totals,
                "session_hour_coverage": session_hour_coverage,
                "strongest_hour": strongest_hour,
                "weakest_hour": weakest_hour,
                "strongest_day": strongest_day,
                "weakest_day": weakest_day,
                "strongest_strategy_window": strongest_strategy_window,
            },
            "findings": [self._serialize_finding(finding) for finding in findings],
            "strengths": [self._serialize_finding(finding) for finding in strengths],
        }

    def _aggregate_trade_hours(self, trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        buckets: Dict[int, Dict[str, float]] = defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0, "wins": 0, "losses": 0})
        for trade in trades:
            hour = self._coerce_hour(trade.get("entry_hour"), trade.get("entry_time"))
            if hour is None:
                continue
            pnl = float(trade.get("net_pnl") or 0.0)
            bucket = buckets[hour]
            bucket["trade_count"] += 1
            bucket["net_pnl"] += pnl
            outcome = classify_trade_outcome(pnl, bool(trade.get("is_closed", True)))
            if outcome == "win":
                bucket["wins"] += 1
            elif outcome == "loss":
                bucket["losses"] += 1
        return {
            self._hour_label(hour): {
                **stats,
                "average_net_pnl": round(stats["net_pnl"] / max(stats["trade_count"], 1), 6),
                "hour": hour,
                "label": self._hour_label(hour),
            }
            for hour, stats in sorted(buckets.items())
        }

    def _aggregate_trade_days(self, trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0, "wins": 0, "losses": 0})
        for trade in trades:
            day = trade.get("entry_day_of_week") or self._coerce_day(trade.get("entry_time"))
            if not day:
                continue
            pnl = float(trade.get("net_pnl") or 0.0)
            bucket = buckets[str(day)]
            bucket["trade_count"] += 1
            bucket["net_pnl"] += pnl
            outcome = classify_trade_outcome(pnl, bool(trade.get("is_closed", True)))
            if outcome == "win":
                bucket["wins"] += 1
            elif outcome == "loss":
                bucket["losses"] += 1
        return {
            day: {
                **stats,
                "average_net_pnl": round(stats["net_pnl"] / max(stats["trade_count"], 1), 6),
                "label": day,
            }
            for day, stats in buckets.items()
        }

    def _aggregate_strategy_hours(self, trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        buckets: Dict[str, Dict[int, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0})
        )
        for trade in trades:
            strategy = trade.get("strategy_tag") or trade.get("strategy") or trade.get("setup_name")
            hour = self._coerce_hour(trade.get("entry_hour"), trade.get("entry_time"))
            if not strategy or hour is None:
                continue
            pnl = float(trade.get("net_pnl") or 0.0)
            bucket = buckets[str(strategy)][hour]
            bucket["trade_count"] += 1
            bucket["net_pnl"] += pnl
        result: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for strategy, hour_map in buckets.items():
            result[strategy] = {
                self._hour_label(hour): {
                    **stats,
                    "average_net_pnl": round(stats["net_pnl"] / max(stats["trade_count"], 1), 6),
                    "hour": hour,
                    "label": self._hour_label(hour),
                    "strategy_tag": strategy,
                }
                for hour, stats in sorted(hour_map.items())
            }
        return result

    def _aggregate_session_daily_minutes(self, sessions: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = defaultdict(float)
        for session in sessions:
            local_date = session.get("local_date")
            if not local_date:
                continue
            totals[str(local_date)] += float(session.get("duration_minutes") or 0.0)
        return {date: round(minutes, 2) for date, minutes in sorted(totals.items())}

    def _aggregate_session_hour_coverage(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        coverage: Dict[int, int] = defaultdict(int)
        for session in sessions:
            opened_at = self._coerce_datetime(session.get("opened_at"))
            closed_at = self._coerce_datetime(session.get("closed_at")) or opened_at
            if opened_at is None:
                continue
            start_hour = opened_at.hour
            end_hour = closed_at.hour if closed_at else start_hour
            for hour in range(min(start_hour, end_hour), max(start_hour, end_hour) + 1):
                coverage[hour] += 1
        return {self._hour_label(hour): count for hour, count in sorted(coverage.items())}

    def _pick_extreme(
        self,
        stats: Dict[str, Dict[str, Any]],
        *,
        highest: bool,
    ) -> Optional[Dict[str, Any]]:
        if not stats:
            return None
        key = max if highest else min
        return key(
            stats.values(),
            key=lambda item: (item.get("average_net_pnl", 0.0), item.get("trade_count", 0))
            if highest
            else (item.get("average_net_pnl", 0.0), -item.get("trade_count", 0)),
        )

    def _pick_best_strategy_window(
        self,
        strategy_hour_stats: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        best: Optional[Dict[str, Any]] = None
        for windows in strategy_hour_stats.values():
            for window in windows.values():
                if best is None or (
                    window.get("average_net_pnl", 0.0),
                    window.get("trade_count", 0),
                ) > (
                    best.get("average_net_pnl", 0.0),
                    best.get("trade_count", 0),
                ):
                    best = window
        return best

    def _detect_underused_profitable_window(
        self,
        strongest_hour: Optional[Dict[str, Any]],
        session_hour_coverage: Dict[str, int],
    ) -> Optional[Dict[str, Any]]:
        if strongest_hour is None or not session_hour_coverage:
            return None
        label = strongest_hour["label"]
        if label not in session_hour_coverage or strongest_hour["trade_count"] < 2:
            return None
        baseline = sum(session_hour_coverage.values()) / max(len(session_hour_coverage), 1)
        actual = session_hour_coverage[label]
        if baseline <= 0:
            return None
        coverage_ratio = round(actual / baseline, 3)
        if strongest_hour["average_net_pnl"] <= 0 or coverage_ratio >= 0.85:
            return None
        return {
            **strongest_hour,
            "coverage_ratio": coverage_ratio,
            "baseline_coverage_ratio": 1.0,
        }

    def _detect_low_time_vs_baseline(
        self,
        session_daily_totals: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        if len(session_daily_totals) < 3:
            return None
        ordered_days = sorted(session_daily_totals.items())
        recent_date, recent_minutes = ordered_days[-1]
        historical_minutes = [minutes for _, minutes in ordered_days[:-1]]
        baseline = sum(historical_minutes) / max(len(historical_minutes), 1)
        if baseline <= 0 or recent_minutes >= baseline * 0.6:
            return None
        return {
            "recent_date": recent_date,
            "recent_minutes": round(recent_minutes, 2),
            "baseline_minutes": round(baseline, 2),
        }

    def _serialize_finding(self, finding: DiagnosticFinding) -> Dict[str, Any]:
        return {
            "category": finding.category,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "metric_reference": finding.metric_reference,
            "value": finding.value,
            "threshold": finding.threshold,
            "metadata": finding.metadata,
        }

    def _coerce_hour(self, explicit_hour: Any, timestamp: Any) -> Optional[int]:
        if isinstance(explicit_hour, int):
            return explicit_hour
        dt = self._coerce_datetime(timestamp)
        return dt.hour if dt else None

    def _coerce_day(self, timestamp: Any) -> Optional[str]:
        dt = self._coerce_datetime(timestamp)
        return dt.strftime("%A") if dt else None

    def _coerce_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    def _hour_label(self, hour: int) -> str:
        return f"{int(hour):02d}:00"

    def _empty_payload(self) -> Dict[str, Any]:
        return {"features": {}, "findings": [], "strengths": []}
