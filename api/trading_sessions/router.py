from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user
from persistence_layer.session_time_utils import minutes_within_local_day, session_local_days


router = APIRouter(prefix="/trading-sessions", tags=["trading-sessions"])


class OpenSessionRequest(BaseModel):
    account_id: str
    broker_id: str
    platform_name: str
    timezone_name: str = "UTC"
    opened_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CloseSessionRequest(BaseModel):
    account_id: str
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("")
def list_trading_sessions(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        sessions = api_registry.trading_platform_session_repository.list_by_account(account_id)
        return {"sessions": [session.to_dict() for session in sessions]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/active")
def get_active_trading_session(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {"active_session": api_registry.platform_session_tracker.get_active_session(account_id)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/daily-totals")
def get_daily_session_totals(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        sessions = api_registry.trading_platform_session_repository.list_by_account(account_id)
        totals: Dict[str, Dict[str, Any]] = {}
        for session in sessions:
            for day in session_local_days(session):
                minutes = minutes_within_local_day(session, day)
                if minutes <= 0:
                    continue
                bucket = totals.setdefault(day, {"day": day, "total_platform_time_minutes": 0.0, "platform_session_count": 0})
                bucket["total_platform_time_minutes"] += minutes
                bucket["platform_session_count"] += 1
        for bucket in totals.values():
            bucket["total_platform_time_minutes"] = round(min(bucket["total_platform_time_minutes"], 1440.0), 2)
        return {"daily_totals": [totals[key] for key in sorted(totals)]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/open")
def open_trading_session(request: OpenSessionRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        session = api_registry.platform_session_tracker.open_session(
            account_id=request.account_id,
            broker_id=request.broker_id,
            platform_name=request.platform_name,
            timezone_name=request.timezone_name,
            opened_at=request.opened_at or datetime.now(timezone.utc),
            metadata=request.metadata,
        )
        return {"session": session}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/close")
def close_trading_session(request: CloseSessionRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        session = api_registry.platform_session_tracker.close_session(
            account_id=request.account_id,
            closed_at=request.closed_at or datetime.now(timezone.utc),
            metadata=request.metadata,
        )
        return {"session": session}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
