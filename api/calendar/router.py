from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user
from models.calendar_view import CalendarColorState, CalendarDaySummary


router = APIRouter(prefix="/calendar", tags=["calendar"])


class CreateDaySummaryRequest(BaseModel):
    account_id: str
    day: str
    pnl: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    discipline_score: Optional[float] = None
    state_key: Optional[str] = None
    notes_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateColorStateRequest(BaseModel):
    account_id: str
    key: str
    color: str
    label: Optional[str] = None


@router.post("/day-summary")
def create_day_summary(request: CreateDaySummaryRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        summary = CalendarDaySummary(**request.model_dump())
        api_registry.calendar_repository.save_day_summary(summary)
        return {"day_summary": summary.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/day-summary")
def list_day_summaries(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "day_summaries": [
                summary.to_dict()
                for summary in api_registry.calendar_repository.list_day_summaries(account_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/day-detail")
def get_day_detail(account_id: str, day: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return api_registry.calendar_day_detail_service.get_day_detail(account_id=account_id, day=day)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/color-state")
def create_color_state(request: CreateColorStateRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        state = CalendarColorState(key=request.key, color=request.color, label=request.label)
        api_registry.calendar_repository.save_color_state(request.account_id, state)
        return {"color_state": state.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/color-state")
def list_color_states(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "color_states": [
                state.to_dict()
                for state in api_registry.calendar_repository.list_color_states(account_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rebuild")
def rebuild_calendar(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "day_summaries": api_registry.calendar_aggregation_engine.rebuild_for_account(account_id)
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
