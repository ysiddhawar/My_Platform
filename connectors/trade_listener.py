from __future__ import annotations

from typing import Dict, Any, Optional
from threading import RLock
from datetime import datetime, timezone

from core.context import Context
from models.trade import Trade
from models.execution_event import ExecutionEvent

from connectors.execution_event_bus import ExecutionEventBus
from execution_tools.execution_orchestrator import ExecutionOrchestrator
from persistence_layer.trade_repository import TradeRepository
from persistence_layer.screenshot_capture_service import ScreenshotCaptureService


class TradeListenerError(Exception):
    pass


class TradeListener:
    """
    Institutional Broker Trade Listener

    Responsibilities:
    - Receive normalized broker events
    - Route pre-trade requests to ExecutionOrchestrator
    - Convert filled trades into Trade model
    - Update context safely
    - Emit execution events
    - Ensure idempotency
    """

    def __init__(
        self,
        context: Context,
        orchestrator: ExecutionOrchestrator,
        event_bus: ExecutionEventBus,
        trade_repository: Optional[TradeRepository] = None,
        screenshot_capture_service: Optional[ScreenshotCaptureService] = None,
    ):
        self._lock = RLock()
        self.context = context
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.trade_repository = trade_repository
        self.screenshot_capture_service = screenshot_capture_service

        self._processed_event_ids = set()

    # ==========================================================
    # MAIN ENTRY
    # ==========================================================

    def on_broker_event(self, event: Dict[str, Any]) -> Dict[str, Any]:

        with self._lock:

            self._validate_event(event)

            event_id = event.get("event_id")

            if event_id in self._processed_event_ids:
                return {"status": "duplicate_ignored"}

            self._processed_event_ids.add(event_id)

            event_type = event.get("type")

            if event_type == "PRE_TRADE_REQUEST":
                return self._handle_pre_trade(event)

            if event_type == "TRADE_FILLED":
                return self._handle_trade_filled(event)

            if event_type == "TRADE_CLOSED":
                return self._handle_trade_closed(event)

            return {"status": "unknown_event_type"}

    # ==========================================================
    # PRE-TRADE ROUTING
    # ==========================================================

    def _handle_pre_trade(self, event: Dict[str, Any]) -> Dict[str, Any]:

        trade_request = event.get("payload")

        result = self.orchestrator.execute_trade(trade_request)

        self.event_bus.emit(
            ExecutionEvent(
                event_type="PRE_TRADE_PROCESSED",
                timestamp=datetime.now(timezone.utc),
                metadata=result,
            )
        )

        return result

    # ==========================================================
    # TRADE FILLED
    # ==========================================================

    def _handle_trade_filled(self, event: Dict[str, Any]) -> Dict[str, Any]:

        payload = dict(event.get("payload") or {})
        active_session = self.context.get_cache("active_platform_session")
        if active_session:
            payload.setdefault("platform_session_id", active_session.get("session_id"))
            metadata = dict(payload.get("metadata") or {})
            metadata.setdefault("platform_session_id", active_session.get("session_id"))
            metadata.setdefault("platform_name", active_session.get("platform_name"))
            payload["metadata"] = metadata
        trade = Trade.from_dict(payload)

        self._store_trade(trade)

        self.event_bus.emit(
            ExecutionEvent(
                event_type="TRADE_RECORDED",
                timestamp=datetime.now(timezone.utc),
                metadata={"trade_id": trade.trade_id},
            )
        )

        return {"status": "trade_recorded", "trade_id": trade.trade_id}

    # ==========================================================
    # TRADE CLOSED
    # ==========================================================

    def _handle_trade_closed(self, event: Dict[str, Any]) -> Dict[str, Any]:

        payload = event.get("payload")
        trade_id = payload.get("trade_id")

        trades = self.context.get_cache("trades") or []
        trade_found = False

        for trade in trades:
            if trade.trade_id == trade_id:
                trade.close_trade(
                    exit_price=payload.get("exit_price"),
                    exit_time=payload.get("exit_time"),
                    exit_reason=payload.get("exit_reason"),
                    slippage_at_exit=payload.get("slippage_at_exit", 0.0),
                    checklist_after=payload.get("selected_checklist") or payload.get("checklist_after"),
                    probability_bucket=payload.get("probability_bucket"),
                    post_trade_capture=payload.get("post_trade_capture"),
                    close_classification=payload.get("close_classification"),
                    notes=payload.get("notes"),
                )
                if payload.get("line_snapshot"):
                    trade.add_line_snapshot(payload["line_snapshot"])
                if self.trade_repository is not None:
                    self.trade_repository.save_trade(trade)
                trade_found = True
                break

        if not trade_found and self.trade_repository is not None:
            stored_trade = self.trade_repository.get_trade(trade_id)
            if stored_trade is not None:
                stored_trade.close_trade(
                    exit_price=payload.get("exit_price"),
                    exit_time=payload.get("exit_time"),
                    exit_reason=payload.get("exit_reason"),
                    slippage_at_exit=payload.get("slippage_at_exit", 0.0),
                    checklist_after=payload.get("selected_checklist") or payload.get("checklist_after"),
                    probability_bucket=payload.get("probability_bucket"),
                    post_trade_capture=payload.get("post_trade_capture"),
                    close_classification=payload.get("close_classification"),
                    notes=payload.get("notes"),
                )
                if payload.get("line_snapshot"):
                    stored_trade.add_line_snapshot(payload["line_snapshot"])
                trades.append(stored_trade)
                self.trade_repository.save_trade(stored_trade)

        self.context.set_cache("trades", trades)

        self.event_bus.emit(
            ExecutionEvent(
                event_type="TRADE_CLOSED_RECORDED",
                timestamp=datetime.now(timezone.utc),
                metadata={"trade_id": trade_id},
            )
        )

        auto_capture_enabled = payload.get("request_screenshot", True)
        capture_request = None
        if auto_capture_enabled and self.screenshot_capture_service is not None:
            try:
                capture_request = self.screenshot_capture_service.request_for_trade(
                    trade_id=trade_id,
                    requested_by=payload.get("requested_by", "system"),
                    trigger="trade_closed",
                    source_hint=payload.get("screenshot_source_type"),
                    metadata={"source_event_id": event.get("event_id")},
                )
                self.event_bus.emit(
                    ExecutionEvent(
                        event_type="SCREENSHOT_CAPTURE_REQUESTED",
                        timestamp=datetime.now(timezone.utc),
                        metadata={
                            "trade_id": trade_id,
                            "request_id": capture_request["request_id"],
                        },
                    )
                )
            except Exception:
                capture_request = None

        return {
            "status": "trade_closed_updated",
            "screenshot_capture_request": capture_request,
        }

    # ==========================================================
    # STORAGE
    # ==========================================================

    def _store_trade(self, trade: Trade):

        trades = self.context.get_cache("trades") or []
        trades.append(trade)
        self.context.set_cache("trades", trades)
        if self.trade_repository is not None:
            self.trade_repository.save_trade(trade)

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def _validate_event(self, event: Dict[str, Any]):

        if not isinstance(event, dict):
            raise TradeListenerError("Event must be dict")

        if "event_id" not in event:
            raise TradeListenerError("Missing event_id")

        if "type" not in event:
            raise TradeListenerError("Missing event type")

        if "payload" not in event:
            raise TradeListenerError("Missing event payload")
