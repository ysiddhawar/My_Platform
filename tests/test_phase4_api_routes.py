import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from api.calendar.router import get_day_detail
from api.missed_opportunities.router import (
    CreateMissedOpportunityRequest,
    create_missed_opportunity,
)
from api.server.api_registry import api_registry
from api.trading_sessions.router import (
    CloseSessionRequest,
    OpenSessionRequest,
    close_trading_session,
    get_daily_session_totals,
    open_trading_session,
)
from execution_tools.missed_opportunity_capture_service import MissedOpportunityCaptureService
from execution_tools.platform_session_tracker import PlatformSessionTracker
from execution_tools.position_sizer import PositionSizer
from models.account import Account
from models.calendar_view import CalendarDaySummary
from models.journal_note import JournalNote
from models.trade import Trade
from persistence_layer.account_repository import AccountRepository
from persistence_layer.calendar_day_detail_service import CalendarDayDetailService
from persistence_layer.calendar_repository import CalendarRepository
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository


class Phase4APIRoutesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.account_repository = AccountRepository(db_path=str(base / "accounts.db"))
        self.trade_repository = TradeRepository(db_path=str(base / "trades.db"))
        self.note_repository = NoteRepository(db_path=str(base / "notes.db"))
        self.calendar_repository = CalendarRepository(db_path=str(base / "calendar.db"))
        self.session_repository = TradingPlatformSessionRepository(db_path=str(base / "sessions.db"))
        self.missed_repository = MissedOpportunityRepository(db_path=str(base / "missed.db"))
        self.platform_session_tracker = PlatformSessionTracker(self.session_repository)
        self.missed_capture_service = MissedOpportunityCaptureService(
            repository=self.missed_repository,
            position_sizer=PositionSizer(),
        )
        self.day_detail_service = CalendarDayDetailService(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            calendar_repository=self.calendar_repository,
            trading_platform_session_repository=self.session_repository,
            missed_opportunity_repository=self.missed_repository,
        )

        self._originals = {
            "account_repository": api_registry.account_repository,
            "trade_repository": api_registry.trade_repository,
            "note_repository": api_registry.note_repository,
            "calendar_repository": api_registry.calendar_repository,
            "trading_platform_session_repository": api_registry.trading_platform_session_repository,
            "missed_opportunity_repository": api_registry.missed_opportunity_repository,
            "platform_session_tracker": api_registry.platform_session_tracker,
            "missed_opportunity_capture_service": api_registry.missed_opportunity_capture_service,
            "calendar_day_detail_service": api_registry.calendar_day_detail_service,
        }

        api_registry.account_repository = self.account_repository
        api_registry.trade_repository = self.trade_repository
        api_registry.note_repository = self.note_repository
        api_registry.calendar_repository = self.calendar_repository
        api_registry.trading_platform_session_repository = self.session_repository
        api_registry.missed_opportunity_repository = self.missed_repository
        api_registry.platform_session_tracker = self.platform_session_tracker
        api_registry.missed_opportunity_capture_service = self.missed_capture_service
        api_registry.calendar_day_detail_service = self.day_detail_service

        self.user = {"account_ids": ["ACC-PHASE4"], "roles": ["user"]}
        self.account = Account(
            broker_id="BRK-4",
            account_name="Phase4",
            initial_balance=15000.0,
            metadata={"timezone_name": "Asia/Kolkata"},
        )
        self.account._account_id = "ACC-PHASE4"
        self.account_repository.save(self.account)

    def tearDown(self):
        for key, value in self._originals.items():
            setattr(api_registry, key, value)

        self.missed_repository.close()
        self.session_repository.close()
        self.calendar_repository.close()
        self.note_repository.close()
        self.trade_repository.close()
        self.account_repository.close()
        self._tmp.cleanup()

    def test_session_routes_and_calendar_day_detail(self):
        opened = open_trading_session(
            OpenSessionRequest(
                account_id="ACC-PHASE4",
                broker_id="BRK-4",
                platform_name="mt5",
                timezone_name="Asia/Kolkata",
                opened_at=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
            ),
            user=self.user,
        )
        self.assertEqual(opened["session"]["account_id"], "ACC-PHASE4")

        closed = close_trading_session(
            CloseSessionRequest(
                account_id="ACC-PHASE4",
                closed_at=datetime(2026, 3, 11, 11, 0, tzinfo=timezone.utc),
            ),
            user=self.user,
        )
        self.assertEqual(closed["session"]["duration_minutes"], 120.0)

        trade = Trade(
            account_id="ACC-PHASE4",
            broker_id="BRK-4",
            symbol="EURUSD",
            market_type="forex",
            side="buy",
            strategy_tag="breakout",
            setup_name="Breakout A",
            entry_price=1.1000,
            quantity=10000,
            lot_size=1.0,
            leverage_used=10.0,
            stop_loss_at_entry=1.0950,
            target_at_entry=1.1120,
            entry_time=datetime(2026, 3, 11, 9, 15, tzinfo=timezone.utc),
        )
        trade.close_trade(
            exit_price=1.1100,
            exit_time=datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc),
            exit_reason="target",
        )
        self.trade_repository.save_trade(trade)

        self.note_repository.save(
            JournalNote(
                account_id="ACC-PHASE4",
                note_type="day_note",
                title="Review",
                body="Good discipline",
                note_date="2026-03-11",
            )
        )
        self.calendar_repository.save_day_summary(
            CalendarDaySummary(
                account_id="ACC-PHASE4",
                day="2026-03-11",
                pnl=trade.to_dict()["net_pnl"],
                gross_pnl=trade.to_dict()["gross_pnl"],
                total_cost=trade.to_dict()["total_cost"],
                trade_count=1,
                win_count=1,
                loss_count=0,
                total_platform_time_minutes=120.0,
                platform_session_count=1,
                missed_opportunity_count=0,
            )
        )

        detail = get_day_detail(account_id="ACC-PHASE4", day="2026-03-11", user=self.user)
        self.assertEqual(detail["display_state"]["key"], "profit")
        self.assertEqual(detail["trade_count"], 1)
        self.assertEqual(len(detail["platform_sessions"]), 1)
        self.assertEqual(len(detail["notes"]), 1)
        self.assertEqual(detail["total_platform_time_minutes"], 120.0)

        totals = get_daily_session_totals(account_id="ACC-PHASE4", user=self.user)
        self.assertEqual(totals["daily_totals"][0]["total_platform_time_minutes"], 120.0)

    def test_create_missed_opportunity_route_uses_account_balance(self):
        created = create_missed_opportunity(
            CreateMissedOpportunityRequest(
                account_id="ACC-PHASE4",
                symbol="EURUSD",
                market_type="forex",
                side="buy",
                strategy_name="Breakout A",
                probability_bucket="60%",
                entry_price=1.1000,
                stop_loss_price=1.0950,
                target_price=1.1120,
                observed_at=datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc),
                timezone_name="Asia/Kolkata",
                metadata={"captured_from": "app"},
            ),
            user=self.user,
        )

        payload = created["missed_opportunity"]
        self.assertEqual(payload["account_id"], "ACC-PHASE4")
        self.assertIsNotNone(payload["minimum_target_price"])
        self.assertEqual(payload["metadata"]["captured_from"], "app")
        self.assertIn("position_plan", payload["metadata"])

    def test_calendar_day_detail_falls_back_to_live_summary_when_stored_summary_is_stale(self):
        trade = Trade(
            account_id="ACC-PHASE4",
            broker_id="BRK-4",
            symbol="EURUSD",
            market_type="forex",
            side="buy",
            strategy_tag="breakout",
            setup_name="Breakout A",
            entry_price=1.1000,
            quantity=10000,
            lot_size=1.0,
            leverage_used=10.0,
            stop_loss_at_entry=1.0950,
            target_at_entry=1.1120,
            entry_time=datetime(2026, 3, 12, 9, 15, tzinfo=timezone.utc),
        )
        trade.close_trade(
            exit_price=1.1100,
            exit_time=datetime(2026, 3, 12, 10, 0, tzinfo=timezone.utc),
            exit_reason="target",
        )
        self.trade_repository.save_trade(trade)
        self.calendar_repository.save_day_summary(
            CalendarDaySummary(
                account_id="ACC-PHASE4",
                day="2026-03-12",
                pnl=0.0,
                trade_count=0,
                total_platform_time_minutes=0.0,
            )
        )

        detail = get_day_detail(account_id="ACC-PHASE4", day="2026-03-12", user=self.user)

        self.assertEqual(detail["summary_source"], "live")
        self.assertEqual(detail["summary"]["trade_count"], 1)
        self.assertEqual(detail["display_state"]["key"], "profit")


if __name__ == "__main__":
    unittest.main()
