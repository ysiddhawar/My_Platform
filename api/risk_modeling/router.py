from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry


router = APIRouter(prefix="/risk-modeling", tags=["risk-modeling"])


class RiskModelingRequest(BaseModel):
    metrics: Dict[str, Dict[str, Any]]
    returns: List[float]
    initial_equity: float


class RiskModelingResponse(BaseModel):
    report: Dict[str, Any]


@router.post("/analyze", response_model=RiskModelingResponse)
def analyze_risk(request: RiskModelingRequest):
    try:
        report = api_registry.risk_modeling_engine.analyze(
            metrics=request.metrics,
            returns=request.returns,
            initial_equity=request.initial_equity,
        )
        return RiskModelingResponse(report=report)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
