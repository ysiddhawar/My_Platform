from __future__ import annotations

from statistics import mean, pstdev
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.missed_opportunity_analyzer import MissedOpportunityAnalyzer
from ai.time_pattern_analyzer import TimePatternAnalyzer
from core.context import Context
from models.missed_opportunity import MissedOpportunity
from models.trade import Trade
from models.trading_platform_session import TradingPlatformSession


class BehavioralAnalyzerError(Exception):
    pass


class BehavioralAnalyzer:
    """
    Adaptive behavioral signal extractor with contextual time intelligence.

    This module still computes the core behavioral metrics, but it now also
    extracts session-time and missed-opportunity intelligence so later AI
    stages can reason across more of the trader's real activity footprint.
    """

    MIN_SAMPLE_SIZE = 10

    def __init__(
        self,
        time_pattern_analyzer: Optional[TimePatternAnalyzer] = None,
        missed_opportunity_analyzer: Optional[MissedOpportunityAnalyzer] = None,
    ):
        self._time_pattern_analyzer = time_pattern_analyzer or TimePatternAnalyzer()
        self._missed_opportunity_analyzer = (
            missed_opportunity_analyzer or MissedOpportunityAnalyzer()
        )

    def analyze(
        self,
        context: Context,
        lookback: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not isinstance(context, Context):
            raise BehavioralAnalyzerError("context must be Context")

        trades = context.get_cache("trades") or []
        violations: List[Dict[str, Any]] = context.get_cache("violations") or []
        discipline_scores: List[float] = context.get_cache("discipline_scores") or []
        sessions = context.get_cache("trading_platform_sessions") or []
        missed_opportunities = context.get_cache("missed_opportunities") or []

        if lookback:
            trades = trades[-lookback:]
            discipline_scores = discipline_scores[-lookback:]

        normalized_trades = [self._normalize_trade(trade) for trade in trades]
        normalized_sessions = [self._normalize_session(session) for session in sessions]
        normalized_opportunities = [
            self._normalize_missed_opportunity(opportunity)
            for opportunity in missed_opportunities
        ]
        cutoff = self._derive_cutoff(normalized_trades) if lookback else None
        if cutoff is not None:
            normalized_sessions = [
                session for session in normalized_sessions
                if self._session_overlaps_cutoff(session, cutoff)
            ]
            normalized_opportunities = [
                opportunity for opportunity in normalized_opportunities
                if self._coerce_timestamp(opportunity.get("observed_at")) is not None
                and self._coerce_timestamp(opportunity.get("observed_at")) >= cutoff
            ]

        time_intelligence = self._time_pattern_analyzer.analyze(
            normalized_trades,
            normalized_sessions,
        )
        missed_opportunity_intelligence = self._missed_opportunity_analyzer.analyze(
            normalized_trades,
            normalized_sessions,
            normalized_opportunities,
        )

        if not normalized_trades:
            return {
                "signals": {},
                "percentiles": {},
                "zscores": {},
                "time_intelligence": time_intelligence,
                "missed_opportunity_intelligence": missed_opportunity_intelligence,
            }

        signals = self._compute_raw_signals(
            normalized_trades,
            violations,
            discipline_scores,
        )
        percentiles = self._compute_percentiles(signals, normalized_trades)
        zscores = self._compute_zscores(signals, normalized_trades)

        return {
            "signals": signals,
            "percentiles": percentiles,
            "zscores": zscores,
            "time_intelligence": time_intelligence,
            "missed_opportunity_intelligence": missed_opportunity_intelligence,
        }

    def _compute_raw_signals(
        self,
        trades: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
        discipline_scores: List[float],
    ) -> Dict[str, float]:
        loss_streak = self._compute_loss_streak(trades)
        risk_drift = self._compute_risk_drift(trades)
        strategy_switch_freq = self._compute_strategy_switching(trades)
        position_size_volatility = self._compute_position_size_volatility(trades)
        violation_frequency = len(violations) / max(1, len(trades))
        discipline_trend = self._compute_trend(discipline_scores)
        early_exit_rate = self._compute_early_exit_rate(trades)
        checklist_compliance = self._compute_checklist_compliance(trades)
        setup_drift_rate = self._compute_setup_drift_rate(trades)
        notes_density = self._compute_notes_density(trades)

        return {
            "loss_streak_length": loss_streak,
            "risk_drift": risk_drift,
            "strategy_switch_frequency": strategy_switch_freq,
            "position_size_volatility": position_size_volatility,
            "violation_frequency": violation_frequency,
            "discipline_score_trend": discipline_trend,
            "trade_frequency": len(trades),
            "early_exit_rate": early_exit_rate,
            "checklist_compliance_rate": checklist_compliance,
            "setup_drift_rate": setup_drift_rate,
            "notes_density": notes_density,
        }

    def _compute_loss_streak(self, trades: List[Dict[str, Any]]) -> int:
        streak = 0
        max_streak = 0
        for trade in trades:
            if self._coerce_number(trade.get("net_pnl")) < 0:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        return max_streak

    def _compute_risk_drift(self, trades: List[Dict[str, Any]]) -> float:
        risks = [
            self._coerce_number(t.get("risk_amount"))
            for t in trades
            if "risk_amount" in t and t.get("risk_amount") is not None
        ]
        if len(risks) < 2:
            return 0.0
        return risks[-1] - mean(risks[:-1])

    def _compute_strategy_switching(self, trades: List[Dict[str, Any]]) -> float:
        switches = 0
        for i in range(1, len(trades)):
            current = trades[i].get("strategy_tag") or trades[i].get("strategy")
            previous = trades[i - 1].get("strategy_tag") or trades[i - 1].get("strategy")
            if current != previous:
                switches += 1
        return switches / max(1, len(trades))

    def _compute_position_size_volatility(self, trades: List[Dict[str, Any]]) -> float:
        sizes = [self._coerce_number(t.get("quantity")) for t in trades]
        if len(sizes) < 2:
            return 0.0
        return pstdev(sizes)

    def _compute_trend(self, series: List[float]) -> float:
        if len(series) < 2:
            return 0.0
        return series[-1] - series[0]

    def _compute_early_exit_rate(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        early_exits = sum(1 for trade in trades if trade.get("closed_before_plan"))
        return early_exits / len(trades)

    def _compute_checklist_compliance(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        compliant = 0
        counted = 0
        for trade in trades:
            capture = trade.get("pre_trade_capture") or {}
            mandatory = capture.get("mandatory_checklist") or []
            selected = capture.get("selected_checklist") or []
            if not mandatory:
                continue
            counted += 1
            if set(mandatory).issubset(set(selected)):
                compliant += 1
        if counted == 0:
            return 0.0
        return compliant / counted

    def _compute_setup_drift_rate(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        drift = 0
        for trade in trades:
            pre_trade = trade.get("pre_trade_capture") or {}
            post_trade = trade.get("post_trade_capture") or {}
            if not pre_trade or not post_trade:
                continue
            if (
                pre_trade.get("strategy_name") != post_trade.get("strategy_name")
                or pre_trade.get("probability_bucket") != post_trade.get("probability_bucket")
            ):
                drift += 1
        return drift / len(trades)

    def _compute_notes_density(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        count = sum(1 for trade in trades if trade.get("notes"))
        return count / len(trades)

    def _compute_percentiles(
        self,
        signals: Dict[str, float],
        trades: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        percentiles = {}
        for key, value in signals.items():
            historical = [
                t.get(key)
                for t in trades
                if key in t and isinstance(t.get(key), (int, float))
            ]
            if len(historical) < self.MIN_SAMPLE_SIZE:
                continue
            count = sum(1 for item in historical if item <= value)
            percentiles[key] = count / len(historical)
        return percentiles

    def _compute_zscores(
        self,
        signals: Dict[str, float],
        trades: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        zscores = {}
        for key, value in signals.items():
            historical = [
                t.get(key)
                for t in trades
                if key in t and isinstance(t.get(key), (int, float))
            ]
            if len(historical) < self.MIN_SAMPLE_SIZE:
                continue
            mu = mean(historical)
            sigma = pstdev(historical)
            if sigma == 0:
                continue
            zscores[key] = (value - mu) / sigma
        return zscores

    def _normalize_trade(self, trade: Any) -> Dict[str, Any]:
        if isinstance(trade, Trade):
            return trade.to_dict()
        if isinstance(trade, dict):
            return trade
        raise BehavioralAnalyzerError("Unsupported trade record type")

    def _normalize_session(self, session: Any) -> Dict[str, Any]:
        if isinstance(session, TradingPlatformSession):
            return session.to_dict()
        if isinstance(session, dict):
            return session
        raise BehavioralAnalyzerError("Unsupported session record type")

    def _normalize_missed_opportunity(self, opportunity: Any) -> Dict[str, Any]:
        if isinstance(opportunity, MissedOpportunity):
            return opportunity.to_dict()
        if isinstance(opportunity, dict):
            return opportunity
        raise BehavioralAnalyzerError("Unsupported missed opportunity record type")

    def _derive_cutoff(self, trades: List[Dict[str, Any]]) -> Optional[datetime]:
        timestamps = [
            self._coerce_timestamp(trade.get("entry_time"))
            for trade in trades
        ]
        timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
        if not timestamps:
            return None
        return min(timestamps)

    def _coerce_timestamp(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    def _coerce_number(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _session_overlaps_cutoff(self, session: Dict[str, Any], cutoff: datetime) -> bool:
        opened_at = self._coerce_timestamp(session.get("opened_at"))
        closed_at = self._coerce_timestamp(session.get("closed_at"))
        if opened_at is None:
            return False
        if opened_at >= cutoff:
            return True
        if closed_at is None:
            return False
        return closed_at >= cutoff
