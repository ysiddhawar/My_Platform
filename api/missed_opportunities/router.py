from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user


router = APIRouter(prefix="/missed-opportunities", tags=["missed-opportunities"])


class CreateMissedOpportunityRequest(BaseModel):
    account_id: str
    broker_id: Optional[str] = None
    symbol: str
    market_type: str
    side: str
    strategy_name: str
    probability_bucket: str
    entry_price: float
    stop_loss_price: float
    target_price: float
    observed_at: Optional[datetime] = None
    timezone_name: str = "UTC"
    exit_price: Optional[float] = None
    exit_at: Optional[datetime] = None
    exit_reason: Optional[str] = None
    checklist_items: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    instrument_overrides: Dict[str, Any] = Field(default_factory=dict)
    cost_overrides: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("")
def create_missed_opportunity(
    request: CreateMissedOpportunityRequest,
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, request.account_id)
        account = api_registry.account_repository.get(request.account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        broker_id = request.broker_id or account.broker_id
        opportunity = api_registry.missed_opportunity_capture_service.capture(
            account_id=request.account_id,
            broker_id=broker_id,
            symbol=request.symbol,
            market_type=request.market_type,
            side=request.side,
            strategy_name=request.strategy_name,
            probability_bucket=request.probability_bucket,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            target_price=request.target_price,
            account_balance=account.equity,
            observed_at=request.observed_at or datetime.now(timezone.utc),
            timezone_name=request.timezone_name,
            exit_price=request.exit_price,
            exit_at=request.exit_at,
            exit_reason=request.exit_reason,
            checklist_items=request.checklist_items,
            notes=request.notes,
            instrument_overrides=request.instrument_overrides or None,
            cost_overrides=request.cost_overrides or None,
            metadata=request.metadata,
        )
        return {"missed_opportunity": opportunity}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_missed_opportunities(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        opportunities = api_registry.missed_opportunity_repository.list_by_account(account_id)
        return {"missed_opportunities": [opportunity.to_dict() for opportunity in opportunities]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/day/{day}")
def list_missed_opportunities_for_day(day: str, account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        opportunities = api_registry.missed_opportunity_repository.list_by_account_for_day(account_id, day)
        return {"missed_opportunities": [opportunity.to_dict() for opportunity in opportunities]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
