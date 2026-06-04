from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, extract_payload_account_id, get_current_user
from models.account import Account
from models.trade import Trade


router = APIRouter(prefix="/trade-ingestion", tags=["trade-ingestion"])


class TradeEventRequest(BaseModel):
    event_id: str = Field(..., description="Unique idempotency id")
    type: str = Field(..., description="PRE_TRADE_REQUEST | TRADE_FILLED | TRADE_CLOSED")
    payload: Dict[str, Any]


class TradeEventResponse(BaseModel):
    status: str
    result: Dict[str, Any]


class RegisterMT5BridgeRequest(BaseModel):
    account_id: str
    broker_id: str
    inbox_dir: str
    archive_dir: Optional[str] = None
    poll_interval_seconds: float = 0.25


class DisconnectBrokerRequest(BaseModel):
    account_id: str


class RegisterSimulatedAdapterRequest(BaseModel):
    account_id: str
    broker_id: str


class SubmitSimulatedEventRequest(BaseModel):
    account_id: str
    event_type: str
    payload: Dict[str, Any]


class ImportCsvRequest(BaseModel):
    account_id: str = "DEFAULT"
    broker_id: str = "BROKER"
    csv_text: str
    market_type: str = "stock"
    default_strategy_name: str = "CSV Import"
    timezone_name: str = "UTC"


@router.post("/adapters/mt5-file")
def register_mt5_file_bridge(request: RegisterMT5BridgeRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.broker_integration_service.register_mt5_file_bridge(
            account_id=request.account_id,
            broker_id=request.broker_id,
            inbox_dir=request.inbox_dir,
            archive_dir=request.archive_dir,
            poll_interval_seconds=request.poll_interval_seconds,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/adapters/simulated")
def register_simulated_adapter(request: RegisterSimulatedAdapterRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.broker_integration_service.register_simulated_adapter(
            account_id=request.account_id,
            broker_id=request.broker_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/adapters")
def list_broker_integrations(user: dict = Depends(get_current_user)):
    try:
        integrations = api_registry.broker_integration_service.list_integrations()["integrations"]
        if "admin" not in set(user.get("roles", [])):
            allowed_accounts = set(user.get("account_ids", []))
            if "*" not in allowed_accounts:
                integrations = [
                    item for item in integrations if item["account_id"] in allowed_accounts
                ]
        return {"integrations": integrations}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/adapters/simulated/event")
def submit_simulated_event(request: SubmitSimulatedEventRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.broker_integration_service.submit_simulated_event(
            account_id=request.account_id,
            event_type=request.event_type,
            payload=request.payload,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/adapters/disconnect")
def disconnect_broker_integration(request: DisconnectBrokerRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.broker_integration_service.disconnect_account(request.account_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-csv")
def import_trade_csv(request: ImportCsvRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        _ensure_account_exists(request.account_id, request.broker_id)
        imported = 0
        errors = []
        reader = csv.DictReader(io.StringIO(request.csv_text))
        # Resolve account timezone
        account = api_registry.account_repository.get(request.account_id)
        if account is not None:
            account_metadata = account.to_dict().get("metadata") or {}
            timezone_name = account_metadata.get("timezone_name", request.timezone_name)
        else:
            timezone_name = request.timezone_name
        
        for index, row in enumerate(reader, start=2):
            try:
                trade = _trade_from_csv_row(
                    row=row,
                    account_id=request.account_id,
                    broker_id=request.broker_id,
                    market_type=request.market_type,
                    default_strategy_name=request.default_strategy_name,
                    timezone_name=timezone_name,
                )
                api_registry.trade_repository.save_trade(trade)
                imported += 1
            except Exception as exc:
                errors.append({"row": index, "detail": str(exc)})
        return {"status": "ok", "imported_count": imported, "errors": errors}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/events", response_model=TradeEventResponse)
def ingest_trade_event(request: TradeEventRequest, user: dict = Depends(get_current_user)):
    try:
        account_id = extract_payload_account_id(request.payload)
        if account_id:
            ensure_account_access(user, account_id)
        result = api_registry.trade_listener.on_broker_event(request.model_dump())
        return TradeEventResponse(status="ok", result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _ensure_account_exists(account_id: str, broker_id: str) -> None:
    account = api_registry.account_repository.get(account_id)
    if account is not None:
        return
    account = Account(
        broker_id=broker_id,
        account_name=f"Imported {account_id}",
        initial_balance=100000.0,
        risk_level="survival",
    )
    account._account_id = account_id
    api_registry.account_repository.save(account)


def _trade_from_csv_row(
    row: Dict[str, Any],
    account_id: str,
    broker_id: str,
    market_type: str,
    default_strategy_name: str,
    timezone_name: str = "UTC",
) -> Trade:
    normalized = {_normalize_key(key): (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
    symbol = _pick(normalized, "symbol", "ticker", "instrument")
    if not symbol:
        raise ValueError("symbol column required")
    side = (_pick(normalized, "side", "type", "direction") or "buy").lower()
    entry_price = _as_float(_pick(normalized, "entry_price", "entry", "open_price", "buy_price"))
    exit_price_raw = _pick(normalized, "exit_price", "exit", "close_price", "sell_price")
    quantity = _as_float(_pick(normalized, "quantity", "qty", "size", "volume") or 1.0)
    strategy_name = _pick(normalized, "strategy", "strategy_name", "setup", "setup_name") or default_strategy_name
    entry_time = _as_datetime(_pick(normalized, "entry_time", "open_time", "opened_at", "date_time", "date"), timezone_name)
    exit_time = _as_datetime(_pick(normalized, "exit_time", "close_time", "closed_at"), timezone_name)
    stop_loss = _as_optional_float(_pick(normalized, "stop_loss", "stop_loss_price", "sl"))
    target = _as_optional_float(_pick(normalized, "target", "target_price", "tp"))
    commission = _as_optional_float(_pick(normalized, "commission")) or 0.0
    fees = _as_optional_float(_pick(normalized, "fees", "fee")) or 0.0
    swaps = _as_optional_float(_pick(normalized, "swaps", "swap")) or 0.0
    slippage_cost = _as_optional_float(_pick(normalized, "slippage_cost", "slippage")) or 0.0
    probability_bucket = _pick(normalized, "probability_bucket", "probability")
    notes = _pick(normalized, "notes", "comment")
    close_classification = _pick(normalized, "close_classification")
    exit_reason = _pick(normalized, "exit_reason", "reason") or "csv_import"

    if entry_price is None:
        raise ValueError("entry_price required — cannot derive P&L from CSV's NET PNL column, must calculate from price difference")

    trade = Trade.from_dict({
        "account_id": account_id,
        "broker_id": broker_id,
        "symbol": symbol,
        "market_type": market_type or (_pick(normalized, "market_type", "market") or "stock"),
        "side": side,
        "strategy_tag": strategy_name,
        "setup_name": strategy_name,
        "entry_price": entry_price,
        "entry_time": entry_time or datetime.now(timezone.utc),
        "quantity": quantity,
        "lot_size": 1.0,
        "leverage_used": 1.0,
        "stop_loss_at_entry": stop_loss,
        "target_at_entry": target,
        "fees": fees,
        "commission": commission,
        "swaps": swaps,
        "slippage_at_entry": slippage_cost,
        "probability_bucket": probability_bucket,
        "notes": notes,
        "pre_trade_capture": {
            "source": "csv_import",
            "strategy_name": strategy_name,
            "probability_bucket": probability_bucket,
        },
        "metadata": {
            "source": "csv_import",
            "raw_row": normalized,
        },
    })

    exit_price = _as_optional_float(exit_price_raw)
    if exit_price is not None:
        trade.close_trade(
            exit_price=exit_price,
            exit_time=exit_time or entry_time or datetime.now(timezone.utc),
            exit_reason=exit_reason,
            slippage_at_exit=0.0,
            probability_bucket=probability_bucket,
            close_classification=close_classification,
            notes=notes,
        )
    return trade


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _pick(row: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(str(value).replace(",", ""))


def _as_optional_float(value: Any) -> Optional[float]:
    try:
        return _as_float(value)
    except Exception:
        return None


def _as_datetime(value: Any, timezone_name: str = "UTC") -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        if value.tzinfo:
            return value
        return value.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo:
        return parsed
    return parsed.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
