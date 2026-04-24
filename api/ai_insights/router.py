from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user


router = APIRouter(prefix="/ai-insights", tags=["ai-insights"])


class AIInsightsEnvelope(BaseModel):
    insights: Dict[str, Any]


@router.get("/summary", response_model=AIInsightsEnvelope)
def get_ai_insights_summary(
    account_id: str = "DEFAULT",
    lookback: Optional[int] = None,
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, account_id)
        insights = api_registry.ai_insights_orchestrator.run(account_id=account_id, lookback=lookback)
        return AIInsightsEnvelope(insights=insights.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
