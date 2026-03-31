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
    close_classification: Optional[str] = None
    slippage_at_exit: float = 0.0
    line_snapshot: Optional[Dict[str, Any]] = None


@router.post("/execute-trade", response_model=ExecuteTradeResponse)
def execute_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = api_registry.execution_orchestrator.execute_trade(request.model_dump())
        return ExecuteTradeResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/update-config", response_model=UpdateExecutionConfigResponse)
def update_execution_config(request: UpdateExecutionConfigRequest):
    try:
        api_registry.execution_orchestrator.update_config(request.config)
        return UpdateExecutionConfigResponse(status="updated")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/preview-trade", response_model=TradePreviewResponse)
def preview_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        result = api_registry.execution_orchestrator.preview_trade(request.model_dump())
        return TradePreviewResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/record-filled-trade", response_model=ExecuteTradeResponse)
def record_filled_trade(request: ExecuteTradeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        execution_result = api_registry.execution_orchestrator.execute_trade(request.model_dump())
        if execution_result.get("status") != "approved":
            return ExecuteTradeResponse(result=execution_result)
        payload = execution_result["execution_payload"]
        result = api_registry.trade_listener.on_broker_event(
            {
                "event_id": f"filled-{payload['account_id']}-{payload['symbol']}-{payload['entry_price']}",
                "type": "TRADE_FILLED",
                "payload": payload,
            }
        )
        return ExecuteTradeResponse(result={**execution_result, "recording": result})
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
