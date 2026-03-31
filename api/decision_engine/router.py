from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry


router = APIRouter(prefix="/decisions", tags=["decision-engine"])


class DecisionRequest(BaseModel):
    structured_data: Dict[str, Dict[str, Any]]
    base_capital: float
    ai_diagnosis: Optional[Dict[str, Any]] = None


class DecisionResponse(BaseModel):
    decision: Dict[str, Any]


@router.post("/evaluate", response_model=DecisionResponse)
def evaluate_decision(request: DecisionRequest):
    try:
        decision = api_registry.decision_engine.evaluate(
            structured_data=request.structured_data,
            base_capital=request.base_capital,
            ai_diagnosis=request.ai_diagnosis,
        )
        return DecisionResponse(decision=decision)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
