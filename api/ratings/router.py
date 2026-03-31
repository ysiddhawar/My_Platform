from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_trade_access, get_current_user
from models.trade_rating import TradeRating


router = APIRouter(prefix="/ratings", tags=["ratings"])


class CreateRatingRequest(BaseModel):
    account_id: str
    trade_id: str
    rating_value: float
    scale_name: str = "five_point"
    rationale: Optional[str] = None
    rated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("")
def create_rating(request: CreateRatingRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        ensure_trade_access(user, request.trade_id)
        rating = TradeRating(**request.model_dump())
        api_registry.rating_repository.save(rating)
        return {"rating": rating.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}")
def get_trade_rating(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        rating = api_registry.rating_repository.get_for_trade(trade_id)
        return {"rating": rating.to_dict() if rating else None}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
