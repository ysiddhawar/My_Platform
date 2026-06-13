from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from core.trade_outcome import is_loss, is_win
from models.calendar_view import CalendarDaySummary
from persistence_layer.calendar_repository import CalendarRepository
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.session_time_utils import minutes_within_local_day, session_local_days
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository
from persistence_layer.trade_repository import TradeRepository


class CalendarAggregationEngine:
    def __init__(
        self,
        trade_repository: TradeRepository,
        note_repository: NoteRepository,
        calendar_repository: CalendarRepository,
        trading_platform_session_repository: TradingPlatformSessionRepository | None = None,
        missed_opportunity_repository: MissedOpportunityRepository | None = None,
    ):
        self._trade_repository = trade_repository
        self._note_repository = note_repository
        self._calendar_repository = calendar_repository
        self._trading_platform_session_repository = trading_platform_session_repository
        self._missed_opportunity_repository = missed_opportunity_repository

    def rebuild_for_account(self, account_id: str) -> List[Dict]:
        trades = [trade.to_dict() for trade in self._trade_repository.get_trades_by_account(account_id)]
        grouped = defaultdict(list)
        for trade in trades:
            entry_day = trade.get("entry_date")
            if not entry_day:
                continue
            grouped[str(entry_day)].append(trade)

        notes = self._note_repository.get_by_account(account_id)
        notes_count_by_day = defaultdict(int)
        for note in notes:
            if note.note_date:
                notes_count_by_day[note.note_date] += 1

        sessions_by_day = defaultdict(list)
        if self._trading_platform_session_repository is not None:
            for session in self._trading_platform_session_repository.list_by_account(account_id):
                for day in session_local_days(session):
                    sessions_by_day[day].append(session)

        missed_by_day = defaultdict(list)
        if self._missed_opportunity_repository is not None:
            for opportunity in self._missed_opportunity_repository.list_by_account(account_id):
                missed_by_day[opportunity.local_date].append(opportunity)

        results = []
        all_days = set(grouped) | set(notes_count_by_day) | set(sessions_by_day) | set(missed_by_day)
        for day in sorted(all_days):
            day_trades = grouped.get(day, [])
            day_sessions = sessions_by_day.get(day, [])
            day_missed = missed_by_day.get(day, [])
            pnl = sum(float(trade.get("net_pnl") or 0.0) for trade in day_trades)
            gross_pnl = sum(float(trade.get("gross_pnl") or 0.0) for trade in day_trades)
            total_cost = sum(float(trade.get("total_cost") or 0.0) for trade in day_trades)
            closed_day_trades = [trade for trade in day_trades if trade.get("is_closed")]
            win_count = sum(1 for trade in closed_day_trades if is_win(trade.get("net_pnl")))
            loss_count = sum(1 for trade in closed_day_trades if is_loss(trade.get("net_pnl")))
            discipline_scores = [
                float((trade.get("pre_trade_capture") or {}).get("metadata", {}).get("discipline_score"))
                for trade in day_trades
                if (trade.get("pre_trade_capture") or {}).get("metadata", {}).get("discipline_score") is not None
            ]
            avg_discipline = sum(discipline_scores) / len(discipline_scores) if discipline_scores else None
            state_key = "positive" if pnl > 0 else "negative" if pnl < 0 else "flat"
            total_platform_time_minutes = round(
                min(sum(minutes_within_local_day(session, day) for session in day_sessions), 1440.0),
                2,
            )
            summary = CalendarDaySummary(
                account_id=account_id,
                day=day,
                pnl=pnl,
                gross_pnl=gross_pnl,
                total_cost=total_cost,
                trade_count=len(day_trades),
                win_count=win_count,
                loss_count=loss_count,
                total_platform_time_minutes=total_platform_time_minutes,
                platform_session_count=len(day_sessions),
                missed_opportunity_count=len(day_missed),
                discipline_score=avg_discipline,
                state_key=state_key,
                notes_count=notes_count_by_day.get(day, 0),
                metadata={
                    "day_of_week": day_trades[0].get("entry_day_of_week") if day_trades else (day_sessions[0].local_day_of_week if day_sessions else (day_missed[0].local_day_of_week if day_missed else None)),
                },
            )
            self._calendar_repository.save_day_summary(summary)
            results.append(summary.to_dict())
        return results
