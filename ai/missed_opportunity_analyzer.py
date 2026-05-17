from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from models.ai_diagnosis import DiagnosticFinding


class MissedOpportunityAnalyzer:
    """
    Analyzes non-executed but recognized setups as a behavioral signal layer.
    """

    def analyze(
        self,
        trades: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not opportunities:
            return self._empty_payload()

        with_platform_context = [
            self._attach_platform_state(opportunity, sessions)
            for opportunity in opportunities
        ]
        by_strategy = self._count_by_key(with_platform_context, "strategy_name")
        by_day = self._count_by_key(with_platform_context, "local_day_of_week")
        by_hour = self._count_by_key(with_platform_context, "observed_hour")
        open_count = sum(1 for item in with_platform_context if item["recorded_while_platform_open"])
        closed_count = len(with_platform_context) - open_count

        profitable_hours = self._profitable_hours(trades)
        profitable_strategies = self._profitable_strategies(trades)
        top_strategy_gap = self._top_overlap(by_strategy, profitable_strategies, "strategy")
        top_hour_gap = self._top_overlap(by_hour, profitable_hours, "hour")

        findings: List[DiagnosticFinding] = []
        strengths: List[DiagnosticFinding] = []

        if len(with_platform_context) >= 2 and closed_count > open_count:
            findings.append(
                DiagnosticFinding(
                    category="missed_opportunity",
                    title="Missed setups occurring away from active platform time",
                    description=(
                        "More missed opportunities are being recorded outside active trading-platform sessions than during live screen time."
                    ),
                    severity="medium",
                    metric_reference="missed_while_platform_closed",
                    value=closed_count,
                    threshold=open_count,
                    metadata={
                        "recorded_while_platform_open": open_count,
                        "recorded_while_platform_closed": closed_count,
                    },
                )
            )

        if top_strategy_gap is not None:
            findings.append(
                DiagnosticFinding(
                    category="missed_opportunity",
                    title="Profitable strategy opportunity gap",
                    description=(
                        f"{top_strategy_gap['label']} is both profitable in executed trades and heavily represented in missed opportunities."
                    ),
                    severity="high",
                    metric_reference="missed_profitable_strategy",
                    value=top_strategy_gap["missed_count"],
                    metadata=top_strategy_gap,
                )
            )

        if top_hour_gap is not None:
            findings.append(
                DiagnosticFinding(
                    category="missed_opportunity",
                    title="Profitable time window opportunity gap",
                    description=(
                        f"Missed opportunities are clustering around {top_hour_gap['label']}, which is also a profitable execution window."
                    ),
                    severity="medium",
                    metric_reference="missed_profitable_hour",
                    value=top_hour_gap["missed_count"],
                    metadata=top_hour_gap,
                )
            )

        if len(with_platform_context) >= max(3, len(trades) or 1):
            findings.append(
                DiagnosticFinding(
                    category="missed_opportunity",
                    title="Recognition is outrunning execution",
                    description=(
                        "The volume of missed opportunities is elevated relative to executed trades, suggesting hesitation or workflow friction."
                    ),
                    severity="medium",
                    metric_reference="missed_to_trade_ratio",
                    value=round(len(with_platform_context) / max(len(trades), 1), 3),
                    threshold=1.0,
                )
            )

        if len(with_platform_context) <= max(1, len(trades) // 4):
            strengths.append(
                DiagnosticFinding(
                    category="missed_opportunity",
                    title="Missed-opportunity load is controlled",
                    description=(
                        "Recognized setups are being executed at a healthy rate relative to the recent trade sample."
                    ),
                    severity="info",
                    metric_reference="missed_to_trade_ratio",
                    value=round(len(with_platform_context) / max(len(trades), 1), 3),
                    threshold=0.25,
                )
            )

        return {
            "features": {
                "total_missed_opportunities": len(with_platform_context),
                "recorded_while_platform_open": open_count,
                "recorded_while_platform_closed": closed_count,
                "by_strategy": by_strategy,
                "by_day": by_day,
                "by_hour": by_hour,
                "profitable_hours": profitable_hours,
                "profitable_strategies": profitable_strategies,
            },
            "findings": [self._serialize_finding(finding) for finding in findings],
            "strengths": [self._serialize_finding(finding) for finding in strengths],
        }

    def _attach_platform_state(
        self,
        opportunity: Dict[str, Any],
        sessions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        observed_at = self._coerce_datetime(opportunity.get("observed_at"))
        account_id = opportunity.get("account_id")
        is_open = False
        if observed_at is not None:
            for session in sessions:
                if session.get("account_id") != account_id:
                    continue
                opened_at = self._coerce_datetime(session.get("opened_at"))
                if opened_at is None:
                    continue
                closed_at = self._coerce_datetime(session.get("closed_at"))
                if closed_at is None:
                    closed_at = opened_at
                if opened_at <= observed_at <= closed_at:
                    is_open = True
                    break
        merged = dict(opportunity)
        merged["recorded_while_platform_open"] = is_open
        return merged

    def _count_by_key(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for row in rows:
            value = row.get(key)
            if value is None:
                continue
            counts[str(value)] += 1
        return dict(sorted(counts.items()))

    def _profitable_hours(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = defaultdict(float)
        counts: Dict[str, int] = defaultdict(int)
        for trade in trades:
            hour = trade.get("entry_hour")
            if hour is None:
                continue
            label = f"{int(hour):02d}:00"
            totals[label] += float(trade.get("net_pnl") or 0.0)
            counts[label] += 1
        return {
            label: round(totals[label] / max(counts[label], 1), 6)
            for label in sorted(totals)
            if totals[label] / max(counts[label], 1) > 0
        }

    def _profitable_strategies(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = defaultdict(float)
        counts: Dict[str, int] = defaultdict(int)
        for trade in trades:
            strategy = trade.get("strategy_tag") or trade.get("strategy") or trade.get("setup_name")
            if not strategy:
                continue
            totals[str(strategy)] += float(trade.get("net_pnl") or 0.0)
            counts[str(strategy)] += 1
        return {
            strategy: round(totals[strategy] / max(counts[strategy], 1), 6)
            for strategy in sorted(totals)
            if totals[strategy] / max(counts[strategy], 1) > 0
        }

    def _top_overlap(
        self,
        missed_counts: Dict[str, int],
        profitable_map: Dict[str, float],
        label_type: str,
    ) -> Optional[Dict[str, Any]]:
        best: Optional[Dict[str, Any]] = None
        for label, missed_count in missed_counts.items():
            if label not in profitable_map or missed_count < 2:
                continue
            candidate = {
                "label": label,
                "missed_count": missed_count,
                "average_profit": profitable_map[label],
                "type": label_type,
            }
            if best is None or (
                candidate["missed_count"],
                candidate["average_profit"],
            ) > (
                best["missed_count"],
                best["average_profit"],
            ):
                best = candidate
        return best

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

    def _coerce_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    def _empty_payload(self) -> Dict[str, Any]:
        return {"features": {}, "findings": [], "strengths": []}
