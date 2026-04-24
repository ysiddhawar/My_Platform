import json
import tempfile
import time
import unittest
from pathlib import Path

from connectors.account_registry import AccountRegistry
from connectors.broker_adapter import BrokerAdapterRegistry
from connectors.broker_integration_service import BrokerIntegrationService
from models.account import Account
from persistence_layer.account_repository import AccountRepository
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.strategy_repository import StrategyRepository


class BrokerAdapterFlowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.account_repository = AccountRepository(db_path=str(base / "accounts.db"))
        self.trade_repository = TradeRepository(db_path=str(base / "trades.db"))
        self.strategy_repository = StrategyRepository(db_path=str(base / "strategies.db"))
        self.account_registry = AccountRegistry(
            trade_repository=self.trade_repository,
            strategy_repository=self.strategy_repository,
        )
        self.adapter_registry = BrokerAdapterRegistry()
        self.integration_service = BrokerIntegrationService(
            account_repository=self.account_repository,
            account_registry=self.account_registry,
            broker_adapter_registry=self.adapter_registry,
        )
        self.account = Account(
            broker_id="MT5-BROKER",
            account_name="Primary MT5",
            initial_balance=10000.0,
            supported_market_types=["forex"],
        )
        self.account_repository.save(self.account)

    def tearDown(self):
        for account_id in list(self.account_registry.list_accounts()):
            self.account_registry.deregister_account(account_id)
        self.strategy_repository.close()
        self.trade_repository.close()
        self.account_repository.close()
        self._tmp.cleanup()

    def test_mt5_file_bridge_records_trade(self):
        inbox = Path(self._tmp.name) / "mt5_inbox"
        archive = Path(self._tmp.name) / "mt5_archive"
        outbox = Path(self._tmp.name) / "mt5_outbox"
        self.integration_service.register_mt5_file_bridge(
            account_id=self.account.account_id,
            broker_id="MT5-BROKER",
            inbox_dir=str(inbox),
            archive_dir=str(archive),
            outbox_dir=str(outbox),
            poll_interval_seconds=0.05,
        )

        event = {
            "event_type": "TRADE_FILLED",
            "payload": {
                "account_id": self.account.account_id,
                "broker_id": "MT5-BROKER",
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
        }
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "event_001.json").write_text(json.dumps(event), encoding="utf-8")

        deadline = time.time() + 3.0
        recorded = None
        while time.time() < deadline:
            trades = self.trade_repository.get_trades_by_account(self.account.account_id)
            if trades:
                recorded = trades[0]
                break
            time.sleep(0.1)

        self.assertIsNotNone(recorded)
        self.assertEqual(recorded.to_dict()["symbol"], "EURUSD")
        self.assertTrue((archive / "event_001.json").exists())

    def test_mt5_file_bridge_writes_prepared_ticket_to_outbox(self):
        inbox = Path(self._tmp.name) / "mt5_inbox"
        archive = Path(self._tmp.name) / "mt5_archive"
        outbox = Path(self._tmp.name) / "mt5_outbox"
        self.integration_service.register_mt5_file_bridge(
            account_id=self.account.account_id,
            broker_id="MT5-BROKER",
            inbox_dir=str(inbox),
            archive_dir=str(archive),
            outbox_dir=str(outbox),
            poll_interval_seconds=0.05,
        )

        result = self.integration_service.submit_prepared_ticket(
            account_id=self.account.account_id,
            ticket={
                "client_ticket_id": "ticket-123",
                "symbol": "EURUSD",
                "side": "buy",
                "entry_price": 1.1000,
                "stop_loss_at_entry": 1.0950,
                "target_at_entry": 1.1100,
                "quantity": 10000,
            },
        )

        self.assertEqual(result["status"], "submitted_to_broker_bridge")
        self.assertTrue((outbox / "order_ticket_ticket-123.json").exists())

    def test_mt5_fill_merges_prepared_context_but_keeps_actual_entry_snapshot(self):
        inbox = Path(self._tmp.name) / "mt5_inbox"
        archive = Path(self._tmp.name) / "mt5_archive"
        outbox = Path(self._tmp.name) / "mt5_outbox"
        self.integration_service.register_mt5_file_bridge(
            account_id=self.account.account_id,
            broker_id="MT5-BROKER",
            inbox_dir=str(inbox),
            archive_dir=str(archive),
            outbox_dir=str(outbox),
            poll_interval_seconds=0.05,
        )

        context = self.account_registry.get_context(self.account.account_id)
        context.set_cache(
            "prepared_broker_tickets",
            {
                "ticket-merge-1": {
                    "client_ticket_id": "ticket-merge-1",
                    "broker_id": "MT5-BROKER",
                    "symbol": "EURUSD",
                    "market_type": "forex",
                    "side": "buy",
                    "strategy_tag": "London Breakout",
                    "setup_name": "London Breakout",
                    "entry_price": 1.1000,
                    "quantity": 10000,
                    "lot_size": 1.0,
                    "leverage_used": 10.0,
                    "stop_loss_at_entry": 1.0950,
                    "target_at_entry": 1.1100,
                    "checklist_before": ["Breakout confirmed"],
                    "probability_bucket": "60%",
                    "pre_trade_capture": {"strategy_name": "London Breakout"},
                    "metadata": {"prepared_ticket_id": "ticket-merge-1"},
                }
            },
        )

        event = {
            "event_type": "TRADE_FILLED",
            "payload": {
                "client_ticket_id": "ticket-merge-1",
                "broker_id": "MT5-BROKER",
                "symbol": "EURUSD",
                "market_type": "forex",
                "side": "buy",
                "entry_price": 1.1006,
                "entry_time": "2026-04-17T12:35:10Z",
                "quantity": 10000,
                "lot_size": 1.0,
                "leverage_used": 10.0,
                "stop_loss_at_entry": 1.0950,
                "target_at_entry": 1.1100,
            },
        }
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "event_merge_001.json").write_text(json.dumps(event), encoding="utf-8")

        deadline = time.time() + 3.0
        recorded = None
        while time.time() < deadline:
            trades = self.trade_repository.get_trades_by_account(self.account.account_id)
            if trades:
                recorded = trades[0]
                break
            time.sleep(0.1)

        self.assertIsNotNone(recorded)
        payload = recorded.to_dict()
        self.assertEqual(payload["entry_price"], 1.1006)
        self.assertEqual(payload["setup_name"], "London Breakout")
        self.assertEqual(payload["probability_bucket"], "60%")


if __name__ == "__main__":
    unittest.main()
