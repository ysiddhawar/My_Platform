from __future__ import annotations

from typing import Dict, Any, Optional
from threading import RLock
from datetime import datetime, timezone
import uuid

from core.context import Context
from core.execution_engine import ExecutionEngine
from models.execution_event import ExecutionEvent

from execution_tools.position_sizer import PositionSizer
from execution_tools.risk_line_manager import RiskLineManager
from execution_tools.slippage_guard import SlippageGuard
from discipline.execution_gatekeeper import ExecutionGatekeeper


class ExecutionOrchestratorError(Exception):
    pass


class ExecutionOrchestrator:
    """
    Institutional Execution Orchestrator

    Responsibilities:
    - Coordinate discipline + risk + execution layers
    - Ensure atomic validation
    - Prevent partial execution
    - Emit structured execution events
    - Remain deterministic and auditable
    """

    def __init__(
        self,
        context: Context,
        execution_engine: Optional[ExecutionEngine] = None,
        position_sizer: Optional[PositionSizer] = None,
        risk_line_manager: Optional[RiskLineManager] = None,
        slippage_guard: Optional[SlippageGuard] = None,
        discipline_gatekeeper: Optional[ExecutionGatekeeper] = None,
        strategy_repository: Optional[Any] = None,
    ):
        self._lock = RLock()

        self.context = context
        self.execution_engine = execution_engine or ExecutionEngine()
        self.position_sizer = position_sizer or PositionSizer()
        self.risk_line_manager = risk_line_manager or RiskLineManager()
        self.slippage_guard = slippage_guard or SlippageGuard()
        self.discipline_gatekeeper = discipline_gatekeeper
        self.strategy_repository = strategy_repository
        self._paused = False

    # ======================================================
    # PUBLIC ENTRY
    # ======================================================

    def execute_trade(
        self,
        trade_request: Dict[str, Any],
    ) -> Dict[str, Any]:

        with self._lock:

            self._validate_trade_request(trade_request)
            trade_request = self._enrich_trade_request(trade_request)

            # -----------------------------------------
            # 1️⃣ Discipline Validation
            # -----------------------------------------

            discipline_state = self._build_discipline_state(trade_request)
            discipline_allowed = self._is_discipline_allowed(trade_request, discipline_state)

            if not discipline_allowed:
                return self._reject(
                    "DISCIPLINE_BLOCK",
                    metadata={
                        "alerts": discipline_state.get("alerts", []),
                        "missing_fields": discipline_state.get("missing_fields", []),
                    },
                )

            # -----------------------------------------
            # 2️⃣ Risk Line Validation
            # -----------------------------------------

            open_positions = trade_request.get("open_positions", 0)
            correlation_exposure = trade_request.get("correlation_exposure")

            if not self.risk_line_manager.is_trade_allowed(
                open_positions=open_positions,
                correlation_exposure=correlation_exposure,
            ):
                return self._reject("RISK_LIMIT_BLOCK")

            # -----------------------------------------
            # 3️⃣ Execution Guard Validation
            # -----------------------------------------

            if not self.slippage_guard.is_execution_allowed(
                slippage_cost=trade_request.get("slippage_cost"),
                spread=trade_request.get("spread"),
                volatility=trade_request.get("volatility"),
            ):
                return self._reject("EXECUTION_GUARD_BLOCK")

            # -----------------------------------------
            # 4️⃣ Position Size Calculation
            # -----------------------------------------

            position_plan = self.position_sizer.preview_position_plan(
                account_balance=trade_request["account_balance"],
                symbol=trade_request["symbol"],
                market_type=trade_request["market_type"],
                side=trade_request["side"],
                entry_price=trade_request["entry_price"],
                stop_loss_price=trade_request["stop_loss_price"],
                target_price=trade_request.get("target_price"),
                probability_bucket=trade_request.get("probability_bucket"),
                explicit_costs=trade_request.get("cost_overrides"),
                instrument_overrides=trade_request.get("instrument_overrides"),
            )

            # -----------------------------------------
            # 5️⃣ Final Execution Event
            # -----------------------------------------

            event = ExecutionEvent(
                event_type="TRADE_EXECUTION_APPROVED",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "symbol": trade_request.get("symbol"),
                    "side": trade_request.get("side"),
                    "calculated_position_size": position_plan["quantity"],
                    "discipline_state": discipline_state,
                },
            )

            self._emit_event(event)

            return {
                "status": "approved",
                "position_size": position_plan["quantity"],
                "position_plan": position_plan,
                "discipline_state": discipline_state,
                "execution_payload": self._build_execution_payload(
                    trade_request,
                    position_plan,
                    discipline_state,
                ),
            }

    def prepare_order_ticket(
        self,
        trade_request: Dict[str, Any],
    ) -> Dict[str, Any]:

        with self._lock:

            self._validate_trade_request(trade_request)
            trade_request = self._enrich_trade_request(trade_request)

            discipline_state = self._build_discipline_state(trade_request)
            discipline_allowed = self._is_discipline_allowed(trade_request, discipline_state)

            if not discipline_allowed:
                return self._reject(
                    "DISCIPLINE_BLOCK",
                    metadata={
                        "alerts": discipline_state.get("alerts", []),
                        "missing_fields": discipline_state.get("missing_fields", []),
                    },
                )

            open_positions = trade_request.get("open_positions", 0)
            correlation_exposure = trade_request.get("correlation_exposure")

            if not self.risk_line_manager.is_trade_allowed(
                open_positions=open_positions,
                correlation_exposure=correlation_exposure,
            ):
                return self._reject("RISK_LIMIT_BLOCK")

            if not self.slippage_guard.is_execution_allowed(
                slippage_cost=trade_request.get("slippage_cost"),
                spread=trade_request.get("spread"),
                volatility=trade_request.get("volatility"),
            ):
                return self._reject("EXECUTION_GUARD_BLOCK")

            position_plan = self.position_sizer.preview_position_plan(
                account_balance=trade_request["account_balance"],
                symbol=trade_request["symbol"],
                market_type=trade_request["market_type"],
                side=trade_request["side"],
                entry_price=trade_request["entry_price"],
                stop_loss_price=trade_request["stop_loss_price"],
                target_price=trade_request.get("target_price"),
                probability_bucket=trade_request.get("probability_bucket"),
                explicit_costs=trade_request.get("cost_overrides"),
                instrument_overrides=trade_request.get("instrument_overrides"),
            )

            event = ExecutionEvent(
                event_type="BROKER_ORDER_TICKET_PREPARED",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "symbol": trade_request.get("symbol"),
                    "side": trade_request.get("side"),
                    "calculated_position_size": position_plan["quantity"],
                    "mode": "broker_prefill_only",
                },
            )

            self._emit_event(event)

            return {
                "status": "ready",
                "position_size": position_plan["quantity"],
                "position_plan": position_plan,
                "discipline_state": discipline_state,
                "broker_order_ticket": self._build_broker_order_ticket(
                    trade_request,
                    position_plan,
                    discipline_state,
                ),
                "launch": {
                    "provider": trade_request.get("broker_id", "BROKER"),
                    "status": "pending_broker_integration",
                    "supported": False,
                    "message": "Broker ticket launching is enabled for prefill only. Final trade execution must happen inside the broker platform.",
                },
            }

    # ======================================================
    # VALIDATION
    # ======================================================

    def _validate_trade_request(self, trade_request: Dict[str, Any]):

        required_fields = (
            "account_balance",
            "entry_price",
            "stop_loss_price",
            "symbol",
            "side",
        )

        for field in required_fields:
            if field not in trade_request:
                raise ExecutionOrchestratorError(
                    f"Missing required field: {field}"
                )

    # ======================================================
    # REJECTION HANDLER
    # ======================================================

    def _reject(self, reason: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        event = ExecutionEvent(
            event_type="TRADE_EXECUTION_REJECTED",
            timestamp=datetime.now(timezone.utc),
            metadata={"reason": reason, **(metadata or {})},
        )

        self._emit_event(event)

        return {
            "status": "rejected",
            "reason": reason,
            **(metadata or {}),
        }

    def _is_discipline_allowed(self, trade_request: Dict[str, Any], discipline_state: Dict[str, Any]) -> bool:
        if discipline_state.get("blocked"):
            return False
        if self.discipline_gatekeeper is None:
            return True

        gate = self.discipline_gatekeeper
        if hasattr(gate, "is_trade_allowed"):
            return bool(gate.is_trade_allowed(trade_request))

        # Fall back to permissive mode when only process()-style gate exists.
        return True

    def preview_trade(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_trade_request(trade_request)
        trade_request = self._enrich_trade_request(trade_request)
        discipline_state = self._build_discipline_state(trade_request)
        plan = self.position_sizer.preview_position_plan(
            account_balance=trade_request["account_balance"],
            symbol=trade_request["symbol"],
            market_type=trade_request["market_type"],
            side=trade_request["side"],
            entry_price=trade_request["entry_price"],
            stop_loss_price=trade_request["stop_loss_price"],
            target_price=trade_request.get("target_price"),
            probability_bucket=trade_request.get("probability_bucket"),
            explicit_costs=trade_request.get("cost_overrides"),
            instrument_overrides=trade_request.get("instrument_overrides"),
        )
        return {
            "position_plan": plan,
            "discipline_state": discipline_state,
        }

    def _enrich_trade_request(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(trade_request)
        enriched.setdefault("account_id", "DEFAULT")
        enriched.setdefault("broker_id", "BROKER")
        enriched.setdefault("market_type", "stock")
        enriched.setdefault("target_price", enriched.get("target"))
        enriched.setdefault("setup_name", enriched.get("strategy_setup"))
        enriched.setdefault("strategy_tag", enriched.get("strategy_setup"))
        # Normalize optional collections so later payload assembly never trips over explicit nulls.
        enriched["selected_checklist"] = list(enriched.get("selected_checklist") or [])
        enriched["line_history"] = list(enriched.get("line_history") or [])
        enriched["cost_overrides"] = dict(enriched.get("cost_overrides") or {})
        enriched["instrument_overrides"] = dict(enriched.get("instrument_overrides") or {})
        return enriched

    def _build_discipline_state(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        discipline_enabled = self.position_sizer.is_discipline_mode_enabled()
        if not discipline_enabled:
            return {
                "enabled": False,
                "blocked": False,
                "missing_fields": [],
                "alerts": [],
                "strategy": None,
                "selected_checklist": [],
                "mandatory_checklist": [],
            }

        strategy_name = trade_request.get("strategy_setup") or trade_request.get("setup_name")
        probability_bucket = trade_request.get("probability_bucket")
        selected_checklist = trade_request.get("selected_checklist") or []

        missing_fields = []
        if not strategy_name:
            missing_fields.append("strategy_setup")
        if not probability_bucket:
            missing_fields.append("probability_bucket")
        if not selected_checklist:
            missing_fields.append("selected_checklist")

        strategy_payload = None
        mandatory_checklist = []
        checklist_items = []
        if strategy_name and self.strategy_repository is not None:
            strategy_payload = self.strategy_repository.get_strategy(strategy_name)
            if not strategy_payload:
                missing_fields.append("strategy_setup")
            else:
                mandatory_checklist = strategy_payload.get("mandatory_checklist_items", [])
                checklist_items = strategy_payload.get("checklist_items", [])

        incomplete_checklist = bool(mandatory_checklist and not set(mandatory_checklist).issubset(set(selected_checklist)))
        alerts = []
        if missing_fields:
            alerts.append("Strategy/setup, probability, and checklist selections are required before trade placement.")
        if incomplete_checklist:
            alerts.append("Not all strategy checklist criteria were selected. Trade can proceed, but AI will record this as rule deviation.")

        return {
            "enabled": True,
            "blocked": bool(missing_fields),
            "missing_fields": missing_fields,
            "alerts": alerts,
            "strategy": strategy_payload,
            "checklist_items": checklist_items,
            "mandatory_checklist": mandatory_checklist,
            "selected_checklist": selected_checklist,
            "probability_bucket": probability_bucket,
            "all_mandatory_selected": not incomplete_checklist if mandatory_checklist else False,
        }

    def _build_execution_payload(
        self,
        trade_request: Dict[str, Any],
        position_plan: Dict[str, Any],
        discipline_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        strategy_name = trade_request.get("strategy_setup") or trade_request.get("setup_name") or "UNSPECIFIED"
        mandatory_checklist = discipline_state.get("mandatory_checklist", [])
        return {
            "account_id": trade_request["account_id"],
            "broker_id": trade_request["broker_id"],
            "symbol": trade_request["symbol"],
            "market_type": trade_request["market_type"],
            "side": trade_request["side"],
            "strategy_tag": strategy_name,
            "setup_name": strategy_name,
            "entry_price": trade_request["entry_price"],
            "quantity": position_plan["quantity"],
            "lot_size": float(trade_request.get("lot_size", 1.0)),
            "leverage_used": float(trade_request.get("leverage_used", 1.0)),
            "stop_loss_at_entry": trade_request["stop_loss_price"],
            "target_at_entry": trade_request.get("target_price"),
            "entry_spread": float(trade_request.get("spread", 0.0) or 0.0),
            "slippage_at_entry": float(trade_request.get("slippage_cost", 0.0) or 0.0),
            "fees": float(position_plan["estimated_fees"]),
            "commission": float(trade_request.get("commission", 0.0) or 0.0),
            "swaps": float(trade_request.get("swaps", 0.0) or 0.0),
            "checklist_before": list(trade_request.get("selected_checklist", [])),
            "probability_bucket": trade_request.get("probability_bucket"),
            "pre_trade_capture": {
                "phase": "pre_trade",
                "strategy_name": strategy_name,
                "probability_bucket": trade_request.get("probability_bucket"),
                "selected_checklist": list(trade_request.get("selected_checklist", [])),
                "mandatory_checklist": mandatory_checklist,
                "all_criteria_selected": set(mandatory_checklist).issubset(set(trade_request.get("selected_checklist", []))) if mandatory_checklist else False,
                "notes": trade_request.get("notes"),
                "metadata": {
                    "discipline_mode_enabled": discipline_state.get("enabled", False),
                    "alerts": discipline_state.get("alerts", []),
                },
            },
            "line_history": list(trade_request.get("line_history", [])),
            "minimum_target_price": position_plan.get("minimum_target_price"),
            "minimum_target_reward": position_plan.get("minimum_target_reward"),
            "notes": trade_request.get("notes"),
            "metadata": {
                "position_plan": position_plan,
                "discipline_state": discipline_state,
                "strategy_tag": strategy_name,
                "setup_name": strategy_name,
                "broker_id": trade_request["broker_id"],
            },
            "volatility_regime_at_entry": trade_request.get("volatility_regime"),
            "equity_at_entry": trade_request.get("account_balance"),
            "drawdown_at_entry": trade_request.get("drawdown_snapshot"),
            "open_positions_count": trade_request.get("open_positions"),
            "correlation_exposure_snapshot": trade_request.get("correlation_snapshot") or {},
        }

    def _build_broker_order_ticket(
        self,
        trade_request: Dict[str, Any],
        position_plan: Dict[str, Any],
        discipline_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        strategy_name = trade_request.get("strategy_setup") or trade_request.get("setup_name") or "UNSPECIFIED"
        client_ticket_id = str(uuid.uuid4())
        prepared_at = datetime.now(timezone.utc).isoformat()
        return {
            "client_ticket_id": client_ticket_id,
            "prepared_ticket_id": client_ticket_id,
            "prepared_at": prepared_at,
            "command_type": "OPEN_ORDER_TICKET",
            "bridge_contract_version": "2026-04-17",
            "route_mode": "prefill_only",
            "account_id": trade_request["account_id"],
            "broker_id": trade_request["broker_id"],
            "symbol": trade_request["symbol"],
            "market_type": trade_request["market_type"],
            "side": trade_request["side"],
            "order_type": trade_request.get("order_type", "market"),
            "entry_price": trade_request["entry_price"],
            "planned_entry_price": trade_request["entry_price"],
            "stop_loss_price": trade_request["stop_loss_price"],
            "stop_loss_at_entry": trade_request["stop_loss_price"],
            "target_price": trade_request.get("target_price"),
            "target_at_entry": trade_request.get("target_price"),
            "quantity": position_plan["quantity"],
            "lot_size": float(trade_request.get("lot_size", 1.0)),
            "leverage_used": float(trade_request.get("leverage_used", 1.0)),
            "strategy_tag": strategy_name,
            "strategy_setup": strategy_name,
            "setup_name": strategy_name,
            "probability_bucket": trade_request.get("probability_bucket"),
            "selected_checklist": list(trade_request.get("selected_checklist", [])),
            "checklist_before": list(trade_request.get("selected_checklist", [])),
            "notes": trade_request.get("notes"),
            "pre_trade_capture": {
                "phase": "pre_trade",
                "strategy_name": strategy_name,
                "probability_bucket": trade_request.get("probability_bucket"),
                "selected_checklist": list(trade_request.get("selected_checklist", [])),
                "mandatory_checklist": discipline_state.get("mandatory_checklist", []),
                "all_criteria_selected": discipline_state.get("all_mandatory_selected", False),
                "notes": trade_request.get("notes"),
                "metadata": {
                    "discipline_mode_enabled": discipline_state.get("enabled", False),
                    "alerts": discipline_state.get("alerts", []),
                },
            },
            "line_history": list(trade_request.get("line_history", [])),
            "minimum_target_price": position_plan.get("minimum_target_price"),
            "minimum_target_reward": position_plan.get("minimum_target_reward"),
            "metadata": {
                "prepared_ticket_id": client_ticket_id,
                "planned_by": "position_sizer",
                "position_plan": position_plan,
                "discipline_state": discipline_state,
                "broker_id": trade_request["broker_id"],
            },
            "position_plan": position_plan,
            "discipline_state": discipline_state,
        }

    def _emit_event(self, event: ExecutionEvent):
        if not self.execution_engine:
            return
        if hasattr(self.execution_engine, "process_event"):
            self.execution_engine.process_event(event)

    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        payload = event.get("payload", {})

        if event_type == "PRE_TRADE_REQUEST":
            return self.execute_trade(payload)

        return {"status": "ignored", "reason": "unsupported_event"}

    def update_config(self, new_config: Dict[str, Any]):
        if not isinstance(new_config, dict):
            return

        position_cfg = new_config.get("position_sizer", {})
        risk_cfg = new_config.get("risk_line_manager", {})
        slippage_cfg = new_config.get("slippage_guard", {})

        if isinstance(position_cfg, dict) and position_cfg:
            self.position_sizer.update_config(**position_cfg)
        if isinstance(risk_cfg, dict) and risk_cfg:
            self.risk_line_manager.update_config(**risk_cfg)
        if isinstance(slippage_cfg, dict) and slippage_cfg:
            self.slippage_guard.update_config(**slippage_cfg)

    def resume(self):
        self._paused = False

    def enter_safe_mode(self):
        self._paused = True
