from __future__ import annotations

from typing import Any, Dict, Optional

from connectors.account_registry import AccountRegistry
from connectors.broker_adapter import BrokerAdapterRegistry
from connectors.mt5_file_bridge_adapter import MT5FileBridgeAdapter
from connectors.simulated_broker_adapter import SimulatedBrokerAdapter
from persistence_layer.account_repository import AccountRepository


class BrokerIntegrationService:
    def __init__(
        self,
        account_repository: AccountRepository,
        account_registry: AccountRegistry,
        broker_adapter_registry: BrokerAdapterRegistry,
    ):
        self._account_repository = account_repository
        self._account_registry = account_registry
        self._broker_adapter_registry = broker_adapter_registry

    def register_mt5_file_bridge(
        self,
        account_id: str,
        broker_id: str,
        inbox_dir: str,
        archive_dir: Optional[str] = None,
        poll_interval_seconds: float = 0.25,
    ) -> Dict[str, Any]:
        account = self._account_repository.get(account_id)
        if account is None:
            raise ValueError("Account not found")

        adapter = MT5FileBridgeAdapter(
            broker_id=broker_id,
            inbox_dir=inbox_dir,
            archive_dir=archive_dir,
            poll_interval_seconds=poll_interval_seconds,
        )
        self._broker_adapter_registry.register(broker_id, adapter)
        self._account_registry.register_account(account=account, adapter=adapter)
        return {
            "broker_id": broker_id,
            "account_id": account_id,
            "adapter_type": "mt5_file_bridge",
            "inbox_dir": inbox_dir,
            "archive_dir": archive_dir or f"{inbox_dir}/processed",
            "connected": adapter.is_connected(),
        }

    def register_simulated_adapter(
        self,
        account_id: str,
        broker_id: str,
    ) -> Dict[str, Any]:
        account = self._account_repository.get(account_id)
        if account is None:
            raise ValueError("Account not found")

        adapter = SimulatedBrokerAdapter(broker_id=broker_id)
        self._broker_adapter_registry.register(broker_id, adapter)
        self._account_registry.register_account(account=account, adapter=adapter)
        return {
            "broker_id": broker_id,
            "account_id": account_id,
            "adapter_type": "simulated_broker",
            "connected": adapter.is_connected(),
        }

    def list_integrations(self) -> Dict[str, Any]:
        integrations = []
        for account_id in self._account_registry.list_accounts():
            container = self._account_registry.get_container(account_id)
            integrations.append(
                {
                    "account_id": account_id,
                    "broker_id": container.account.broker_id,
                    "adapter_type": container.adapter.__class__.__name__,
                    "connected": container.adapter.is_connected(),
                }
            )
        return {"integrations": integrations}

    def disconnect_account(self, account_id: str) -> Dict[str, Any]:
        container = self._account_registry.get_container(account_id)
        broker_id = container.account.broker_id
        self._account_registry.deregister_account(account_id)
        self._broker_adapter_registry.unregister(broker_id)
        return {"status": "disconnected", "account_id": account_id, "broker_id": broker_id}

    def submit_simulated_event(
        self,
        account_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        container = self._account_registry.get_container(account_id)
        if not isinstance(container.adapter, SimulatedBrokerAdapter):
            raise ValueError("Account is not using simulated broker adapter")
        container.adapter.push_event(event_type=event_type, payload=payload)
        return {"status": "queued", "account_id": account_id, "event_type": event_type}
