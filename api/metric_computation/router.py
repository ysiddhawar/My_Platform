from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry


router = APIRouter(prefix="/metrics", tags=["metric-computation"])


class MetricRunRequest(BaseModel):
    category: Optional[str] = None
    metrics_subset: Optional[List[str]] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    phase: str = "research"


class MetricRunResponse(BaseModel):
    results: Dict[str, Any]
    errors: Dict[str, Any]
    metadata: Dict[str, Any]


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_to_json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return value


@router.post("/run", response_model=MetricRunResponse)
def run_metrics(request: MetricRunRequest):
    try:
        payload = dict(request.data)
        if isinstance(payload.get("returns"), list):
            payload["returns"] = np.asarray(payload["returns"], dtype=np.float64)

        context = api_registry.execution_engine.run(
            data=payload,
            registry=api_registry.registry,
            category=request.category,
            metrics_subset=request.metrics_subset,
            phase=request.phase,
        )

        return MetricRunResponse(
            results=_to_json_safe(context.all_results()),
            errors=_to_json_safe(context.get_errors()),
            metadata=_to_json_safe(context.metadata()),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
