from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user


router = APIRouter(prefix="/governance-config", tags=["governance-config"])


class ConfigUpdateRequest(BaseModel):
    account_id: str
    config: Dict[str, Any]
    source: str = "api"


class ConfigUpdateResponse(BaseModel):
    status: str
    config_version: int


class ActiveConfigResponse(BaseModel):
    status: str
    active_config: Dict[str, Any] | None


@router.post("/update", response_model=ConfigUpdateResponse)
def update_governance_config(request: ConfigUpdateRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        ts = datetime.now(timezone.utc).isoformat()
        version = api_registry.config_repository.create_new_version(
            account_id=request.account_id,
            config=request.config,
            source=request.source,
            timestamp=ts,
        )
        api_registry.config_repository.activate_version(
            account_id=request.account_id,
            config_version=version,
            timestamp=ts,
        )
        api_registry.execution_orchestrator.update_config(request.config)
        return ConfigUpdateResponse(status="updated", config_version=version)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/active/{account_id}", response_model=ActiveConfigResponse)
def get_active_config(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        cfg = api_registry.config_repository.get_active_config(account_id)
        return ActiveConfigResponse(status="ok", active_config=cfg)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
