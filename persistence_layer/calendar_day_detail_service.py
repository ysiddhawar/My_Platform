from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.trade_outcome import is_loss, is_win
from models.calendar_view import CalendarDaySummary
from persistence_layer.calendar_repository import CalendarRepository
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.session_time_utils import minutes_within_local_day, session_overlaps_local_day
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository


class CalendarDayDetailService:
    def __init__(
        self,
        trade_repository: TradeRepository,
        note_repository: NoteRepository,
        calendar_repository: CalendarRepository,
        trading_platform_session_repository: TradingPlatformSessionRepository,
        missed_opportunity_repository: MissedOpportunityRepository,
    ):
        self._trade_repository = trade_repository
        self._note_repository = note_repository
        self._calendar_repository = calendar_repository
        self._trading_platform_session_repository = trading_platform_session_repository
        self._missed_opportunity_repository = missed_opportunity_repository

    def get_day_detail(self, account_id: str, day: str) -> Dict[str, Any]:
        trades = self._trades_for_day(account_id, day)
        sessions = [
            session
            for session in self._trading_platform_session_repository.list_by_account(account_id)
            if session_overlaps_local_day(session, day)
        ]
        missed_opportunities = self._missed_opportunity_repository.list_by_account_for_day(account_id, day)
        notes = self._notes_for_day(account_id, day)
        stored_summary = self._find_summary(account_id, day)
        live_summary = self._build_live_summary(
            account_id=account_id,
            day=day,
            trades=trades,
            sessions=sessions,
            missed_opportunities=missed_opportunities,
            notes=notes,
        )
        effective_summary = self._effective_summary(stored_summary, live_summary)

        return {
            "day": day,
            "summary": effective_summary.to_dict(),
            "summary_source": self._summary_source(stored_summary, effective_summary),
            "display_state": self._derive_display_state(effective_summary),
            "trade_count": len(trades),
            "net_pnl": round(sum(float(trade.to_dict().get("net_pnl") or 0.0) for trade in trades), 6),
            "gross_pnl": round(sum(float(trade.to_dict().get("gross_pnl") or 0.0) for trade in trades), 6),
            "total_cost": round(sum(float(trade.to_dict().get("total_cost") or 0.0) for trade in trades), 6),
            "total_platform_time_minutes": round(
                min(sum(minutes_within_local_day(session, day) for session in sessions), 1440.0),
                2,
            ),
            "platform_sessions": [
                {
                    **session.to_dict(),
                    "minutes_within_day": minutes_within_local_day(session, day),
                }
                for session in sessions
            ],
            "trades": [trade.to_dict() for trade in trades],
            "missed_opportunities": [opportunity.to_dict() for opportunity in missed_opportunities],
            "notes": [note.to_dict() for note in notes],
        }

    def _find_summary(self, account_id: str, day: str):
        summaries = self._calendar_repository.list_day_summaries(account_id)
        for summary in summaries:
            if summary.day == day:
                return summary
        return None

    def _trades_for_day(self, account_id: str, day: str) -> List[Any]:
        trades = self._trade_repository.get_trades_by_account(account_id)
        result = []
        for trade in trades:
            payload = trade.to_dict()
            entry_date = self._normalize_day(payload.get("entry_date"))
            exit_date = self._normalize_day(payload.get("exit_date"))
            if entry_date == day or exit_date == day:
                result.append(trade)
        return result

    def _notes_for_day(self, account_id: str, day: str) -> List[Any]:
        notes: List[Any] = []
        for note in self._note_repository.get_by_account(account_id):
            payload = note.to_dict()
            if payload.get("note_date") == day:
                notes.append(note)
        return notes

    def _derive_display_state(self, summary: Optional[Any]) -> Dict[str, Any]:
        if summary is None:
            return {"key": "no_data", "color_family": "neutral"}
        if summary.trade_count <= 0 and summary.missed_opportunity_count <= 0 and summary.total_platform_time_minutes <= 0:
            return {"key": "no_trade", "color_family": "neutral"}
        if summary.pnl > 0:
            return {"key": "profit", "color_family": "green"}
        if summary.pnl < 0:
            return {"key": "loss", "color_family": "red"}
        return {"key": "flat", "color_family": "neutral"}

    def _build_live_summary(
        self,
        account_id: str,
        day: str,
        trades: List[Any],
        sessions: List[Any],
        missed_opportunities: List[Any],
        notes: List[Any],
    ) -> CalendarDaySummary:
        net_pnl = round(sum(float(trade.to_dict().get("net_pnl") or 0.0) for trade in trades), 6)
        gross_pnl = round(sum(float(trade.to_dict().get("gross_pnl") or 0.0) for trade in trades), 6)
        total_cost = round(sum(float(trade.to_dict().get("total_cost") or 0.0) for trade in trades), 6)
        closed_trade_dicts = [trade.to_dict() for trade in trades if trade.to_dict().get("is_closed")]
        win_count = sum(1 for trade in closed_trade_dicts if is_win(trade.get("net_pnl")))
        loss_count = sum(1 for trade in closed_trade_dicts if is_loss(trade.get("net_pnl")))
        total_platform_time_minutes = round(
            min(sum(minutes_within_local_day(session, day) for session in sessions), 1440.0),
            2,
        )
        state_key = "positive" if net_pnl > 0 else "negative" if net_pnl < 0 else "flat"
        return CalendarDaySummary(
            account_id=account_id,
            day=day,
            pnl=net_pnl,
            gross_pnl=gross_pnl,
            total_cost=total_cost,
            trade_count=len(trades),
            win_count=win_count,
            loss_count=loss_count,
            total_platform_time_minutes=total_platform_time_minutes,
            platform_session_count=len(sessions),
            missed_opportunity_count=len(missed_opportunities),
            notes_count=len(notes),
            state_key=state_key,
            metadata={},
        )

    def _effective_summary(
        self,
        stored_summary: Optional[CalendarDaySummary],
        live_summary: CalendarDaySummary,
    ) -> CalendarDaySummary:
        if stored_summary is None:
            return live_summary
        if (
            stored_summary.trade_count != live_summary.trade_count
            or round(float(stored_summary.pnl), 6) != round(float(live_summary.pnl), 6)
            or round(float(stored_summary.total_platform_time_minutes), 2) != round(float(live_summary.total_platform_time_minutes), 2)
            or stored_summary.missed_opportunity_count != live_summary.missed_opportunity_count
            or stored_summary.notes_count != live_summary.notes_count
        ):
            return live_summary
        return stored_summary

    def _summary_source(
        self,
        stored_summary: Optional[CalendarDaySummary],
        effective_summary: CalendarDaySummary,
    ) -> str:
        if stored_summary is None:
            return "live"
        return "stored" if stored_summary.to_dict() == effective_summary.to_dict() else "live"

    def _normalize_day(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)
