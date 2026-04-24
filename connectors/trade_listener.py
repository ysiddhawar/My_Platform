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

            if event_type in {"POSITION_MODIFIED", "ORDER_UPDATED"}:
                return self._handle_position_modified(event)

            if event_type == "SCALE_IN":
                return self._handle_scale_in(event)

            if event_type in {"PARTIAL_CLOSE", "SCALE_OUT"}:
                return self._handle_partial_close(event)

            if event_type == "ORDER_CANCELLED":
                return self._handle_order_cancelled(event)

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
        payload = self._merge_prepared_ticket_context(payload)
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

    def _handle_position_modified(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event.get("payload") or {})
        trade = self._find_trade(payload.get("trade_id"))
        if trade is None:
            return {"status": "trade_not_found", "trade_id": payload.get("trade_id")}

        trade.update_position_plan(
            stop_loss_at_entry=payload.get("stop_loss_at_entry"),
            target_at_entry=payload.get("target_at_entry"),
            minimum_target_price=payload.get("minimum_target_price"),
            minimum_target_reward=payload.get("minimum_target_reward"),
            line_snapshot=payload.get("line_snapshot"),
            notes=payload.get("notes"),
            metadata_update={"last_broker_position_update": payload},
            event_type=str(event.get("type") or "POSITION_MODIFIED"),
        )
        self._replace_trade_in_context(trade)
        if self.trade_repository is not None:
            self.trade_repository.save_trade(trade)
        self.event_bus.emit(
            ExecutionEvent(
                event_type="TRADE_POSITION_MODIFIED",
                timestamp=datetime.now(timezone.utc),
                metadata={"trade_id": trade.trade_id},
            )
        )
        return {"status": "trade_position_updated", "trade_id": trade.trade_id}

    def _handle_scale_in(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event.get("payload") or {})
        trade = self._find_trade(payload.get("trade_id"))
        if trade is None:
            return {"status": "trade_not_found", "trade_id": payload.get("trade_id")}

        trade.scale_in(
            additional_quantity=payload.get("additional_quantity") or payload.get("quantity_delta") or payload.get("quantity"),
            fill_price=payload.get("fill_price") or payload.get("entry_price"),
            fees=payload.get("fees", 0.0),
            commission=payload.get("commission", 0.0),
            swaps=payload.get("swaps", 0.0),
            slippage_at_entry=payload.get("slippage_at_entry", 0.0),
            line_snapshot=payload.get("line_snapshot"),
            notes=payload.get("notes"),
            metadata_update={"last_scale_in": payload},
        )
        self._replace_trade_in_context(trade)
        if self.trade_repository is not None:
            self.trade_repository.save_trade(trade)
        self.event_bus.emit(
            ExecutionEvent(
                event_type="TRADE_SCALED_IN",
                timestamp=datetime.now(timezone.utc),
                metadata={"trade_id": trade.trade_id},
            )
        )
        return {"status": "trade_scaled_in", "trade_id": trade.trade_id}

    def _handle_partial_close(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event.get("payload") or {})
        trade = self._find_trade(payload.get("trade_id"))
        if trade is None:
            return {"status": "trade_not_found", "trade_id": payload.get("trade_id")}

        closed_quantity = payload.get("closed_quantity") or payload.get("quantity_delta") or payload.get("quantity")
        if closed_quantity is None:
            return {"status": "invalid_payload", "detail": "closed_quantity is required"}

        if float(closed_quantity) >= float(trade.to_dict().get("quantity") or 0):
            return self._handle_trade_closed(
                {
                    **event,
                    "payload": {
                        **payload,
                        "trade_id": trade.trade_id,
                    },
                }
            )

        partial_trade = trade.create_partial_close_trade(
            closed_quantity=closed_quantity,
            exit_price=payload.get("exit_price"),
            exit_time=payload.get("exit_time"),
            exit_reason=payload.get("exit_reason", "partial_close"),
            slippage_at_exit=payload.get("slippage_at_exit", 0.0),
            checklist_after=payload.get("selected_checklist") or payload.get("checklist_after"),
            probability_bucket=payload.get("probability_bucket"),
            post_trade_capture=payload.get("post_trade_capture"),
            close_classification=payload.get("close_classification"),
            notes=payload.get("notes"),
            line_snapshot=payload.get("line_snapshot"),
            metadata_update={"last_partial_close": payload},
            partial_trade_id=payload.get("partial_trade_id") or f"{trade.trade_id}-partial-{event.get('event_id')}",
        )

        self._replace_trade_in_context(trade)
        self._store_trade(partial_trade)
        if self.trade_repository is not None:
            self.trade_repository.save_trade(trade)
            self.trade_repository.save_trade(partial_trade)
        self.event_bus.emit(
            ExecutionEvent(
                event_type="TRADE_PARTIALLY_CLOSED",
                timestamp=datetime.now(timezone.utc),
                metadata={"trade_id": trade.trade_id, "partial_trade_id": partial_trade.trade_id},
            )
        )
        return {
            "status": "trade_partially_closed",
            "trade_id": trade.trade_id,
            "partial_trade_id": partial_trade.trade_id,
        }

    def _handle_order_cancelled(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event.get("payload") or {})
        broker_activity = list(self.context.get_cache("broker_activity") or [])
        broker_activity.append(
            {
                "type": "ORDER_CANCELLED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
        )
        self.context.set_cache("broker_activity", broker_activity[-200:])
        self.event_bus.emit(
            ExecutionEvent(
                event_type="BROKER_ORDER_CANCELLED",
                timestamp=datetime.now(timezone.utc),
                metadata=payload,
            )
        )
        return {"status": "order_cancelled_recorded"}

    # ==========================================================
    # STORAGE
    # ==========================================================

    def _store_trade(self, trade: Trade):

        trades = self.context.get_cache("trades") or []
        trades = [existing for existing in trades if existing.trade_id != trade.trade_id]
        trades.append(trade)
        self.context.set_cache("trades", trades)
        if self.trade_repository is not None:
            self.trade_repository.save_trade(trade)

    def _replace_trade_in_context(self, trade: Trade):
        trades = self.context.get_cache("trades") or []
        updated = False
        for index, existing in enumerate(trades):
            if existing.trade_id == trade.trade_id:
                trades[index] = trade
                updated = True
                break
        if not updated:
            trades.append(trade)
        self.context.set_cache("trades", trades)

    def _find_trade(self, trade_id: Optional[str]) -> Optional[Trade]:
        if not trade_id:
            return None
        trades = self.context.get_cache("trades") or []
        for trade in trades:
            if trade.trade_id == trade_id:
                return trade
        if self.trade_repository is not None:
            return self.trade_repository.get_trade(trade_id)
        return None

    def _merge_prepared_ticket_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        client_ticket_id = payload.get("client_ticket_id") or payload.get("prepared_ticket_id")
        if not client_ticket_id:
            return payload

        prepared = dict(self.context.get_cache("prepared_broker_tickets") or {})
        pending = prepared.get(str(client_ticket_id))
        if not isinstance(pending, dict):
            return payload

        merged = dict(pending)
        for key, value in payload.items():
            if value is not None:
                merged[key] = value

        pending_pre_trade = dict(pending.get("pre_trade_capture") or {})
        live_pre_trade = dict(payload.get("pre_trade_capture") or {})
        if pending_pre_trade or live_pre_trade:
            merged["pre_trade_capture"] = {**pending_pre_trade, **live_pre_trade}

        pending_metadata = dict(pending.get("metadata") or {})
        live_metadata = dict(payload.get("metadata") or {})
        if pending_metadata or live_metadata:
            merged["metadata"] = {**pending_metadata, **live_metadata}

        prepared.pop(str(client_ticket_id), None)
        self.context.set_cache("prepared_broker_tickets", prepared)
        return merged

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
