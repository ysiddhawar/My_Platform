from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry


router = APIRouter(prefix="/ai-diagnostic", tags=["ai-diagnostic"])


class AIDiagnosticRequest(BaseModel):
    structured_metrics: Dict[str, Dict[str, Any]]
    governance_tier: str
    percentiles: Optional[Dict[str, float]] = None
    zscores: Optional[Dict[str, float]] = None
    behavioral_signals: Optional[Dict[str, Any]] = None
    time_intelligence: Optional[Dict[str, Any]] = None
    missed_opportunity_intelligence: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIDiagnosticResponse(BaseModel):
    diagnosis: Dict[str, Any]


@router.post("/run", response_model=AIDiagnosticResponse)
def run_diagnostic(request: AIDiagnosticRequest):
    try:
        diagnosis = api_registry.diagnostic_orchestrator.run(
            structured_metrics=request.structured_metrics,
            governance_tier=request.governance_tier,
            percentiles=request.percentiles,
            zscores=request.zscores,
            behavioral_signals=request.behavioral_signals,
            time_intelligence=request.time_intelligence,
            missed_opportunity_intelligence=request.missed_opportunity_intelligence,
            metadata=request.metadata,
        )
        return AIDiagnosticResponse(diagnosis=diagnosis.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
