from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_trade_access, get_current_user


router = APIRouter(prefix="/execution-tools", tags=["execution-tools"])


class ExecuteTradeRequest(BaseModel):
    account_balance: float
    entry_price: float
    stop_loss_price: float
    symbol: str
    side: str
    target_price: Optional[float] = None
    account_id: str = "DEFAULT"
    broker_id: str = "BROKER"
    market_type: str = "stock"
    strategy_setup: Optional[str] = None
    probability_bucket: Optional[str] = None
    selected_checklist: Optional[list[str]] = None
    notes: Optional[str] = None
    line_history: Optional[list[Dict[str, Any]]] = None
    cost_overrides: Optional[Dict[str, Any]] = None
    instrument_overrides: Optional[Dict[str, Any]] = None
    slippage_cost: Optional[float] = None
    spread: Optional[float] = None
    volatility: Optional[float] = None
    open_positions: int = 0
    correlation_exposure: Optional[float] = None


class ExecuteTradeResponse(BaseModel):
    result: Dict[str, Any]


class UpdateExecutionConfigRequest(BaseModel):
    config: Dict[str, Any]
    account_id: Optional[str] = None


class UpdateExecutionConfigResponse(BaseModel):
    status: str


class TradePreviewResponse(BaseModel):
    result: Dict[str, Any]


class CloseTradeRequest(BaseModel):
    trade_id: str
    exit_price: float
    exit_reason: str
    exit_time: Optional[str] = None
    probability_bucket: Optional[str] = None
    selected_checklist: Optional[list[str]] = None
    strategy_setup: Optional[str] = None
    notes: Optional[str] = None
    slippage_at_exit: float = 0.0
    line_snapshot: Optional[Dict[str, Any]] = None


def _resolve_orchestrator(account_id: str):
    try:
        return api_registry.account_registry.get_container(account_id).orchestrator
    except Exception:
        return api_registry.execution_orchestrator


def _cache_prepared_ticket(account_id: str, ticket: Dict[str, Any]) -> None:
    try:
        context = api_registry.account_registry.get_context(account_id)
    except Exception:
        return
    prepared = dict(context.get_cache("prepared_broker_tickets") or {})
    client_ticket_id = ticket.get("client_ticket_id") or ticket.get("prepared_ticket_id")
    if client_ticket_id:
        prepared[str(client_ticket_id)] = ticket
        context.set_cache("prepared_broker_tickets", prepared)


@router.post("/execute-trade", response_model=ExecuteTradeResponse)
def execute_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = {
            "status": "disabled",
            "reason": "DIRECT_EXECUTION_DISABLED",
            "detail": "Direct trade routing from the app has been disabled. Use /prepare-order-ticket and complete execution in the broker platform.",
        }
        return ExecuteTradeResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/update-config", response_model=UpdateExecutionConfigResponse)
def update_execution_config(request: UpdateExecutionConfigRequest):
    try:
        orchestrator = _resolve_orchestrator(request.account_id) if request.account_id else api_registry.execution_orchestrator
        orchestrator.update_config(request.config)
        return UpdateExecutionConfigResponse(status="updated")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/preview-trade", response_model=TradePreviewResponse)
def preview_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = _resolve_orchestrator(request.account_id).preview_trade(request.model_dump())
        return TradePreviewResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/prepare-order-ticket", response_model=ExecuteTradeResponse)
def prepare_order_ticket(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = _resolve_orchestrator(request.account_id).prepare_order_ticket(request.model_dump())
        if result.get("status") == "ready" and isinstance(result.get("broker_order_ticket"), dict):
            _cache_prepared_ticket(request.account_id, result["broker_order_ticket"])
            try:
                result["launch"] = api_registry.broker_integration_service.submit_prepared_ticket(
                    request.account_id,
                    result["broker_order_ticket"],
                )
            except Exception as exc:
                result["launch"] = {
                    "provider": request.broker_id or "BROKER",
                    "status": "pending_broker_integration",
                    "supported": False,
                    "message": str(exc),
                }
        return ExecuteTradeResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/record-filled-trade", response_model=ExecuteTradeResponse)
def record_filled_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = {
            "status": "disabled",
            "reason": "DIRECT_EXECUTION_DISABLED",
            "detail": "Filled trades must come from the broker integration event stream, not from the Position Sizer flow.",
        }
        return ExecuteTradeResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/close-trade", response_model=ExecuteTradeResponse)
def close_trade(request: CloseTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, request.trade_id)
        payload = request.model_dump()
        strategy_name = payload.get("strategy_setup")
        strategy = api_registry.strategy_repository.get_strategy(strategy_name) if strategy_name else None
        payload["post_trade_capture"] = {
            "phase": "post_trade",
            "strategy_name": strategy_name,
            "probability_bucket": payload.get("probability_bucket"),
            "selected_checklist": payload.get("selected_checklist") or [],
            "mandatory_checklist": (strategy or {}).get("mandatory_checklist_items", []),
            "all_criteria_selected": set((strategy or {}).get("mandatory_checklist_items", [])).issubset(
                set(payload.get("selected_checklist") or [])
            ) if strategy else False,
            "notes": payload.get("notes"),
        }
        result = api_registry.trade_listener.on_broker_event(
            {
                "event_id": f"closed-{payload['trade_id']}",
                "type": "TRADE_CLOSED",
                "payload": payload,
            }
        )
        return ExecuteTradeResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
