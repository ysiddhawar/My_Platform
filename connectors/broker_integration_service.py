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

    def restore_persisted_integrations(self) -> Dict[str, Any]:
        restored: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for account in self._account_repository.get_all_accounts():
            config = self._extract_persisted_integration_config(account.account_id)
            if not config:
                continue
            try:
                self._ensure_account_connected(account.account_id)
                restored.append({"account_id": account.account_id, "type": config.get("type")})
            except Exception as exc:
                skipped.append({"account_id": account.account_id, "reason": str(exc)})
        return {"restored": restored, "skipped": skipped}

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
                    "inbox_dir": getattr(container.adapter, "inbox_dir", None),
                    "archive_dir": getattr(container.adapter, "archive_dir", None),
                    "health": container.adapter.get_health_snapshot(),
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

    def submit_prepared_ticket(
        self,
        account_id: str,
        ticket: Dict[str, Any],
    ) -> Dict[str, Any]:
        container = self._ensure_account_connected(account_id)
        adapter = container.adapter
        if not adapter.supports_order_ticket_submission():
            try:
                return adapter.submit_order_ticket(ticket)
            except Exception:
                return {
                    "provider": container.account.broker_id,
                    "status": "pending_broker_integration",
                    "supported": False,
                    "message": "This broker connection does not support outbound order ticket submission yet.",
                }
        return adapter.submit_order_ticket(ticket)

    def _ensure_account_connected(self, account_id: str):
        try:
            return self._account_registry.get_container(account_id)
        except Exception:
            config = self._extract_persisted_integration_config(account_id)
            if not config:
                raise ValueError("Account not found")
            integration_type = str(config.get("type") or "").lower()
            if integration_type == "mt5_file_bridge":
                self.register_mt5_file_bridge(
                    account_id=account_id,
                    broker_id=str(config.get("broker_id") or "MT5"),
                    inbox_dir=str(config["inbox_dir"]),
                    archive_dir=config.get("archive_dir"),
                    poll_interval_seconds=float(config.get("poll_interval_seconds") or 0.25),
                )
                return self._account_registry.get_container(account_id)
            if integration_type == "simulated":
                self.register_simulated_adapter(
                    account_id=account_id,
                    broker_id=str(config.get("broker_id") or "BROKER"),
                )
                return self._account_registry.get_container(account_id)
            raise ValueError("Account not found")

    def _extract_persisted_integration_config(self, account_id: str) -> Optional[Dict[str, Any]]:
        account = self._account_repository.get(account_id)
        if account is None:
            return None
        metadata = account.to_dict().get("metadata", {}) or {}
        config = metadata.get("broker_integration")
        if not isinstance(config, dict):
            return None
        return config
