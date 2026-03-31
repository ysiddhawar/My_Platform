from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_admin, get_current_user


router = APIRouter(prefix="/recovery", tags=["recovery"])


class RecoveryRequest(BaseModel):
    account_id: Optional[str] = None


class RecoveryResponse(BaseModel):
    result: Dict[str, Any]


@router.post("/run", response_model=RecoveryResponse)
def run_recovery(request: RecoveryRequest, user: dict = Depends(get_current_user)):
    try:
        if request.account_id:
            ensure_account_access(user, request.account_id)
        else:
            ensure_admin(user)
        result = api_registry.recovery_engine.recover(account_id=request.account_id)
        return RecoveryResponse(result=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
