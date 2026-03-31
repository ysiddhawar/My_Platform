import tempfile
import time
import unittest
from pathlib import Path

from connectors.account_registry import AccountRegistry
from connectors.simulated_broker_adapter import SimulatedBrokerAdapter
from execution_tools.missed_opportunity_capture_service import MissedOpportunityCaptureService
from execution_tools.platform_session_tracker import PlatformSessionTracker
from execution_tools.position_sizer import PositionSizer
from models.account import Account
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository
from persistence_layer.strategy_repository import StrategyRepository
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.trading_platform_session_repository import TradingPlatformSessionRepository


class Phase2SessionAndMissedCaptureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.trade_repository = TradeRepository(db_path=str(base / "trades.db"))
        self.strategy_repository = StrategyRepository(db_path=str(base / "strategies.db"))
        self.session_repository = TradingPlatformSessionRepository(
            db_path=str(base / "sessions.db")
        )
        self.missed_opportunity_repository = MissedOpportunityRepository(
            db_path=str(base / "missed.db")
        )
        self.platform_session_tracker = PlatformSessionTracker(
            session_repository=self.session_repository,
        )
        self.account_registry = AccountRegistry(
            trade_repository=self.trade_repository,
            strategy_repository=self.strategy_repository,
            platform_session_tracker=self.platform_session_tracker,
        )
        self.missed_capture_service = MissedOpportunityCaptureService(
            repository=self.missed_opportunity_repository,
            position_sizer=PositionSizer(),
        )
        self.account = Account(
            broker_id="SIM-BROKER",
            account_name="Primary Sim",
            initial_balance=12000.0,
            supported_market_types=["forex"],
            metadata={"timezone_name": "Asia/Kolkata"},
        )

    def tearDown(self):
        for account_id in list(self.account_registry.list_accounts()):
            self.account_registry.deregister_account(account_id)
        self.missed_opportunity_repository.close()
        self.session_repository.close()
        self.strategy_repository.close()
        self.trade_repository.close()
        self._tmp.cleanup()

    def test_account_registration_opens_and_closes_platform_session(self):
        adapter = SimulatedBrokerAdapter(broker_id="SIM-BROKER")
        self.account_registry.register_account(account=self.account, adapter=adapter)

        active_session = self.platform_session_tracker.get_active_session(self.account.account_id)
        self.assertIsNotNone(active_session)
        self.assertEqual(active_session["platform_name"], "simulatedbroker")
        self.assertEqual(active_session["timezone_name"], "Asia/Kolkata")

        stored_sessions = self.session_repository.list_by_account(self.account.account_id)
        self.assertEqual(len(stored_sessions), 1)
        self.assertIsNone(stored_sessions[0].closed_at)

        adapter.push_event(
            event_type="TRADE_FILLED",
            payload={
                "broker_id": "SIM-BROKER",
                "symbol": "EURUSD",
                "market_type": "forex",
                "side": "buy",
                "strategy": "breakout",
                "setup_name": "London Breakout",
                "entry_price": 1.1000,
                "quantity": 10000,
                "lot_size": 1.0,
                "leverage_used": 10.0,
                "stop_loss_at_entry": 1.0950,
                "target_at_entry": 1.1100,
            },
        )

        deadline = time.time() + 2.0
        recorded_trade = None
        while time.time() < deadline:
            trades = self.trade_repository.get_trades_by_account(self.account.account_id)
            if trades:
                recorded_trade = trades[0]
                break
            time.sleep(0.05)

        self.assertIsNotNone(recorded_trade)
        trade_payload = recorded_trade.to_dict()
        self.assertEqual(
            trade_payload["metadata"]["platform_session_id"],
            active_session["session_id"],
        )

        self.account_registry.deregister_account(self.account.account_id)

        active_after_close = self.platform_session_tracker.get_active_session(self.account.account_id)
        self.assertIsNone(active_after_close)

        closed_sessions = self.session_repository.list_by_account(self.account.account_id)
        self.assertEqual(len(closed_sessions), 1)
        self.assertIsNotNone(closed_sessions[0].closed_at)

    def test_missed_opportunity_capture_persists_minimum_target_plan(self):
        captured = self.missed_capture_service.capture(
            account_id=self.account.account_id,
            broker_id=self.account.broker_id,
            symbol="EURUSD",
            market_type="forex",
            side="buy",
            strategy_name="London Breakout",
            probability_bucket="60%",
            entry_price=1.1000,
            stop_loss_price=1.0950,
            target_price=1.1120,
            account_balance=12000.0,
            timezone_name="Asia/Kolkata",
            metadata={"captured_from": "platform_window"},
        )

        self.assertIsNotNone(captured["minimum_target_price"])
        self.assertEqual(captured["timezone_name"], "Asia/Kolkata")
        self.assertEqual(captured["metadata"]["captured_from"], "platform_window")
        self.assertIn("position_plan", captured["metadata"])
        self.assertEqual(
            captured["metadata"]["position_plan"]["minimum_target_price"],
            captured["minimum_target_price"],
        )

        stored = self.missed_opportunity_repository.get_opportunity(captured["opportunity_id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored.to_dict()["strategy_name"], "London Breakout")

    def test_platform_session_tracker_recovers_open_session_after_restart(self):
        first_tracker = PlatformSessionTracker(session_repository=self.session_repository)
        opened = first_tracker.open_session(
            account_id=self.account.account_id,
            broker_id=self.account.broker_id,
            platform_name="mt5",
            timezone_name="Asia/Kolkata",
        )

        restarted_tracker = PlatformSessionTracker(session_repository=self.session_repository)
        recovered = restarted_tracker.get_active_session(self.account.account_id)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["session_id"], opened["session_id"])

        closed = restarted_tracker.close_session(self.account.account_id)
        self.assertIsNotNone(closed)
        self.assertEqual(closed["session_id"], opened["session_id"])
        self.assertIsNone(restarted_tracker.get_active_session(self.account.account_id))


if __name__ == "__main__":
    unittest.main()
