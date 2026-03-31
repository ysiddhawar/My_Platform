from __future__ import annotations

from typing import Dict, Optional
from threading import RLock

from core.context import Context
from connectors.execution_event_bus import ExecutionEventBus
from connectors.trade_listener import TradeListener
from execution_tools.execution_orchestrator import ExecutionOrchestrator
from execution_tools.platform_session_tracker import PlatformSessionTracker
from connectors.broker_adapter import BaseBrokerAdapter
from models.account import Account
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.screenshot_capture_service import ScreenshotCaptureService
from persistence_layer.strategy_repository import StrategyRepository


class AccountRegistryError(Exception):
    pass


class AccountContainer:
    """
    Internal account wrapper.
    Encapsulates isolated runtime components per account.
    """

    def __init__(
        self,
        account: Account,
        adapter: BaseBrokerAdapter,
        context: Context,
        orchestrator: ExecutionOrchestrator,
        event_bus: ExecutionEventBus,
        trade_listener: TradeListener,
    ):
        self.account = account
        self.adapter = adapter
        self.context = context
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.trade_listener = trade_listener


class AccountRegistry:
    """
    Institutional Multi-Account Registry

    Responsibilities:
    - Register accounts safely
    - Bind broker adapter
    - Create isolated execution stack
    - Maintain context isolation
    - Support runtime config updates
    - Enable account-level governance tier
    """

    def __init__(
        self,
        trade_repository: Optional[TradeRepository] = None,
        screenshot_capture_service: Optional[ScreenshotCaptureService] = None,
        strategy_repository: Optional[StrategyRepository] = None,
        platform_session_tracker: Optional[PlatformSessionTracker] = None,
    ):
        self._lock = RLock()
        self._accounts: Dict[str, AccountContainer] = {}
        self._trade_repository = trade_repository
        self._screenshot_capture_service = screenshot_capture_service
        self._strategy_repository = strategy_repository
        self._platform_session_tracker = platform_session_tracker

    # ==========================================================
    # REGISTRATION
    # ==========================================================

    def register_account(
        self,
        account: Account,
        adapter: BaseBrokerAdapter,
    ):

        with self._lock:

            account_id = account.account_id

            if account_id in self._accounts:
                raise AccountRegistryError("Account already registered")

            # Create isolated context per account
            context = Context()

            # Create execution orchestrator per account
            orchestrator = ExecutionOrchestrator(
                context=context,
                strategy_repository=self._strategy_repository,
            )
            event_bus = ExecutionEventBus()
            trade_listener = TradeListener(
                context=context,
                orchestrator=orchestrator,
                event_bus=event_bus,
                trade_repository=self._trade_repository,
                screenshot_capture_service=self._screenshot_capture_service,
            )

            container = AccountContainer(
                account=account,
                adapter=adapter,
                context=context,
                orchestrator=orchestrator,
                event_bus=event_bus,
                trade_listener=trade_listener,
            )

            self._accounts[account_id] = container

            if self._platform_session_tracker is not None:
                active_session = self._platform_session_tracker.open_session(
                    account_id=account_id,
                    broker_id=account.broker_id,
                    platform_name=self._resolve_platform_name(adapter),
                    timezone_name=self._resolve_timezone_name(account),
                    metadata={
                        "adapter_type": adapter.__class__.__name__,
                        "account_name": account.account_name,
                    },
                )
                context.set_cache("active_platform_session", active_session)

            # Bind adapter event callback to account listener
            adapter.register_event_callback(
                lambda event: self._route_event(account_id, event)
            )

            adapter.connect()

    # ==========================================================
    # EVENT ROUTING
    # ==========================================================

    def _route_event(
        self,
        account_id: str,
        event: dict
    ):

        container = self._accounts.get(account_id)

        if not container:
            return

        # Inject account_id into payload for isolation
        event["payload"]["account_id"] = account_id
        active_session = container.context.get_cache("active_platform_session")
        if active_session:
            event["payload"].setdefault("platform_session_id", active_session.get("session_id"))

        container.trade_listener.on_broker_event(event)

    # ==========================================================
    # CONFIG UPDATE
    # ==========================================================

    def update_account_config(
        self,
        account_id: str,
        new_config: dict,
    ):

        with self._lock:

            container = self._accounts.get(account_id)

            if not container:
                raise AccountRegistryError("Account not found")

            # Update execution controls safely
            container.orchestrator.update_config(new_config)

    # ==========================================================
    # ACCESSORS
    # ==========================================================

    def get_context(self, account_id: str) -> Context:

        container = self._accounts.get(account_id)

        if not container:
            raise AccountRegistryError("Account not found")

        return container.context

    def get_account(self, account_id: str) -> Account:

        container = self._accounts.get(account_id)

        if not container:
            raise AccountRegistryError("Account not found")

        return container.account

    def list_accounts(self):
        return list(self._accounts.keys())

    def get_container(self, account_id: str) -> AccountContainer:
        container = self._accounts.get(account_id)
        if not container:
            raise AccountRegistryError("Account not found")
        return container

    # ==========================================================
    # SAFE DEREGISTRATION
    # ==========================================================

    def deregister_account(self, account_id: str):

        with self._lock:

            container = self._accounts.pop(account_id, None)

            if container:
                if self._platform_session_tracker is not None:
                    closed_session = self._platform_session_tracker.close_session(
                        account_id=account_id,
                        metadata={
                            "adapter_type": container.adapter.__class__.__name__,
                            "disconnected": True,
                        },
                    )
                    container.context.set_cache("active_platform_session", closed_session)
                container.event_bus.shutdown()
                container.adapter.disconnect()

    @staticmethod
    def _resolve_platform_name(adapter: BaseBrokerAdapter) -> str:
        name = adapter.__class__.__name__
        if name.endswith("Adapter"):
            name = name[:-7]
        return name.lower()

    @staticmethod
    def _resolve_timezone_name(account: Account) -> str:
        metadata = account.to_dict().get("metadata", {})
        return (
            metadata.get("timezone_name")
            or metadata.get("timezone")
            or "UTC"
        )
