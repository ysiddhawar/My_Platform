import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from models.missed_opportunity import MissedOpportunity
from models.trade import Trade
from models.trading_platform_session import TradingPlatformSession
from persistence_layer.calendar_aggregation_engine import CalendarAggregationEngine
from persistence_layer.calendar_repository import CalendarRepository
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository


class Phase1TimeAndCalendarTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.trade_repository = TradeRepository(db_path=str(base / 'trades.db'))
        self.note_repository = NoteRepository(db_path=str(base / 'notes.db'))
        self.calendar_repository = CalendarRepository(db_path=str(base / 'calendar.db'))
        self.session_repository = TradingPlatformSessionRepository(db_path=str(base / 'sessions.db'))
        self.missed_repository = MissedOpportunityRepository(db_path=str(base / 'missed.db'))
        self.aggregation_engine = CalendarAggregationEngine(
            trade_repository=self.trade_repository,
            note_repository=self.note_repository,
            calendar_repository=self.calendar_repository,
            trading_platform_session_repository=self.session_repository,
            missed_opportunity_repository=self.missed_repository,
        )

    def tearDown(self):
        self.missed_repository.close()
        self.session_repository.close()
        self.calendar_repository.close()
        self.note_repository.close()
        self.trade_repository.close()
        self._tmp.cleanup()

    def test_phase1_repositories_and_calendar_summary(self):
        entry_time = datetime(2026, 3, 11, 14, 15, tzinfo=timezone.utc)
        trade = Trade(
            account_id='ACC-1',
            broker_id='BRK-1',
            symbol='EURUSD',
            market_type='forex',
            side='buy',
            strategy_tag='breakout',
            setup_name='London Breakout',
            entry_price=1.1,
            quantity=10000,
            lot_size=1.0,
            leverage_used=10.0,
            stop_loss_at_entry=1.095,
            target_at_entry=1.11,
            fees=2.0,
            commission=1.5,
            slippage_at_entry=0.25,
            entry_time=entry_time,
        )
        trade.close_trade(
            exit_price=1.106,
            exit_time=datetime(2026, 3, 11, 15, 0, tzinfo=timezone.utc),
            exit_reason='target_hit',
            slippage_at_exit=0.3,
        )
        self.trade_repository.save_trade(trade)

        session = TradingPlatformSession(
            account_id='ACC-1',
            broker_id='BRK-1',
            platform_name='mt5',
            opened_at=datetime(2026, 3, 11, 14, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 3, 11, 16, 0, tzinfo=timezone.utc),
            timezone_name='UTC',
        )
        self.session_repository.save_session(session)

        missed = MissedOpportunity(
            account_id='ACC-1',
            broker_id='BRK-1',
            symbol='EURUSD',
            market_type='forex',
            side='buy',
            strategy_name='London Breakout',
            probability_bucket='60%',
            entry_price=1.101,
            stop_loss_price=1.096,
            target_price=1.111,
            minimum_target_price=1.108,
            observed_at=datetime(2026, 3, 11, 17, 0, tzinfo=timezone.utc),
            timezone_name='UTC',
            metadata={'platform_open': False},
        )
        self.missed_repository.save_opportunity(missed)

        saved_session = self.session_repository.get_session(session.session_id)
        self.assertIsNotNone(saved_session)
        self.assertEqual(saved_session.duration_minutes, 120.0)

        saved_missed = self.missed_repository.get_opportunity(missed.opportunity_id)
        self.assertIsNotNone(saved_missed)
        self.assertEqual(saved_missed.local_day_of_week, 'Wednesday')

        summaries = self.aggregation_engine.rebuild_for_account('ACC-1')
        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary['day'], '2026-03-11')
        self.assertEqual(summary['trade_count'], 1)
        self.assertEqual(summary['platform_session_count'], 1)
        self.assertEqual(summary['missed_opportunity_count'], 1)
        self.assertEqual(summary['total_platform_time_minutes'], 120.0)
        self.assertGreater(summary['gross_pnl'], 0.0)
        self.assertGreater(summary['total_cost'], 0.0)
        self.assertEqual(summary['metadata']['day_of_week'], 'Wednesday')

        reloaded_trade = self.trade_repository.get_trade(trade.trade_id)
        self.assertIsNotNone(reloaded_trade)
        trade_payload = reloaded_trade.to_dict()
        self.assertEqual(trade_payload['entry_day_of_week'], 'Wednesday')
        self.assertEqual(trade_payload['entry_hour'], 14)
        self.assertEqual(trade_payload['entry_hour_bucket'], '14:00-15:00')
        self.assertEqual(trade_payload['exit_hour'], 15)
        self.assertGreater(trade_payload['total_cost'], 0.0)

    def test_phase1_respects_timezone_name_for_local_bucketing(self):
        session = TradingPlatformSession(
            account_id='ACC-TZ',
            broker_id='BRK-TZ',
            platform_name='mt5',
            opened_at=datetime(2026, 3, 11, 22, 30, tzinfo=timezone.utc),
            closed_at=datetime(2026, 3, 11, 23, 30, tzinfo=timezone.utc),
            timezone_name='Asia/Kolkata',
        )
        opportunity = MissedOpportunity(
            account_id='ACC-TZ',
            broker_id='BRK-TZ',
            symbol='EURUSD',
            market_type='forex',
            side='buy',
            strategy_name='Asia Breakout',
            probability_bucket='60%',
            entry_price=1.1000,
            stop_loss_price=1.0950,
            target_price=1.1120,
            minimum_target_price=1.1060,
            observed_at=datetime(2026, 3, 11, 21, 0, tzinfo=timezone.utc),
            timezone_name='Asia/Kolkata',
        )

        self.assertEqual(session.local_date, '2026-03-12')
        self.assertEqual(session.local_day_of_week, 'Thursday')
        self.assertEqual(session.start_hour, 4)

        self.assertEqual(opportunity.local_date, '2026-03-12')
        self.assertEqual(opportunity.local_day_of_week, 'Thursday')
        self.assertEqual(opportunity.observed_hour, 2)


if __name__ == '__main__':
    unittest.main()
