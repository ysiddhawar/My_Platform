from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from statistics import mean

from models.trade import Trade
from models.discipline_report import DisciplineReport
from discipline.violation_tracker import ViolationTracker


class BehavioralSignalExtractorError(Exception):
    pass


class BehavioralSignalExtractor:
    """
    Institutional Behavioral Signal Extraction Engine

    Extracts structured behavioral signals from:
    - Discipline history
    - Trade history
    - Risk drift
    - Loss streak behavior
    - Trade frequency acceleration
    - Strategy switching
    - Position size volatility

    This engine does NOT classify psychology.
    It only produces quantitative behavioral signals.
    """

    def __init__(self, violation_tracker: ViolationTracker):

        if not isinstance(violation_tracker, ViolationTracker):
            raise BehavioralSignalExtractorError(
                "violation_tracker must be ViolationTracker instance"
            )

        self._tracker = violation_tracker

    # =====================================================
    # MAIN EXTRACTION
    # =====================================================

    def extract(
        self,
        account_id: str,
        trades: List[Trade],
        discipline_reports: List[DisciplineReport],
        lookback_minutes: int = 120,
    ) -> Dict[str, Any]:

        if not isinstance(trades, list):
            raise BehavioralSignalExtractorError("trades must be list")

        if not isinstance(discipline_reports, list):
            raise BehavioralSignalExtractorError("discipline_reports must be list")

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=lookback_minutes)

        recent_trades = [
            t for t in trades
            if t.to_dict().get("entry_date")
            and t.to_dict()["entry_date"] >= cutoff.date()
        ]

        recent_reports = [
            r for r in discipline_reports
            if r.to_dict().get("created_at")
            and r.to_dict()["created_at"].astimezone(timezone.utc) >= cutoff
        ]

        return {
            "trade_frequency": self._compute_trade_frequency(recent_trades, lookback_minutes),
            "loss_streak_length": self._compute_loss_streak(trades),
            "risk_drift": self._compute_risk_drift(trades),
            "position_size_volatility": self._compute_position_size_volatility(trades),
            "strategy_switch_frequency": self._compute_strategy_switching(trades),
            "discipline_score_trend": self._compute_discipline_trend(discipline_reports),
            "violation_frequency": self._compute_violation_frequency(account_id, lookback_minutes),
        }

    # =====================================================
    # SIGNAL COMPONENTS
    # =====================================================

    def _compute_trade_frequency(self, trades: List[Trade], window_minutes: int) -> float:

        if window_minutes <= 0:
            return 0.0

        return round(len(trades) / window_minutes, 4)

    def _compute_loss_streak(self, trades: List[Trade]) -> int:

        streak = 0

        for trade in reversed(trades):
            pnl = trade.to_dict().get("net_pnl")
            if pnl is None:
                continue
            if pnl < 0:
                streak += 1
            else:
                break

        return streak

    def _compute_risk_drift(self, trades: List[Trade]) -> float:

        risk_values = [
            t.to_dict().get("risk_amount")
            for t in trades
            if t.to_dict().get("risk_amount") is not None
        ]

        if len(risk_values) < 2:
            return 0.0

        return round(risk_values[-1] - mean(risk_values[:-1]), 6)

    def _compute_position_size_volatility(self, trades: List[Trade]) -> float:

        sizes = [
            t.to_dict().get("quantity")
            for t in trades
            if t.to_dict().get("quantity") is not None
        ]

        if len(sizes) < 2:
            return 0.0

        avg = mean(sizes)
        variance = mean([(x - avg) ** 2 for x in sizes])

        return round(variance ** 0.5, 6)

    def _compute_strategy_switching(self, trades: List[Trade]) -> float:

        if len(trades) < 2:
            return 0.0

        switches = 0

        for i in range(1, len(trades)):
            prev = trades[i - 1].to_dict().get("strategy_tag")
            curr = trades[i].to_dict().get("strategy_tag")
            if prev != curr:
                switches += 1

        return round(switches / len(trades), 4)

    def _compute_discipline_trend(self, reports: List[DisciplineReport]) -> float:

        scores = [
            r.to_dict().get("discipline_score")
            for r in reports
            if r.to_dict().get("discipline_score") is not None
        ]

        if len(scores) < 2:
            return 0.0

        return round(scores[-1] - mean(scores[:-1]), 4)

    def _compute_violation_frequency(self, account_id: str, window_minutes: int) -> int:

        return self._tracker.get_recent_violations(account_id, window_minutes)
