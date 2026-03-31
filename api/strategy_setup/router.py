from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from models.strategy import Strategy


router = APIRouter(prefix="/strategy-setup", tags=["strategy-setup"])


class CreateStrategyRequest(BaseModel):
    name: str
    description: str
    market_types: List[str]
    checklist_items: List[str]
    mandatory_checklist_items: List[str] = Field(default_factory=list)
    default_risk_percent: float = 1.0
    max_risk_percent: float = 2.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AppendChecklistRequest(BaseModel):
    checklist_items: List[str]
    mandatory_checklist_items: List[str] = Field(default_factory=list)


@router.get("/list")
def list_strategies(active_only: bool = False):
    try:
        return {"strategies": api_registry.strategy_repository.list_strategies(active_only=active_only)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/create")
def create_strategy(request: CreateStrategyRequest):
    try:
        strategy = Strategy(
            name=request.name,
            description=request.description,
            market_types=request.market_types,
            checklist_items=request.checklist_items,
            mandatory_checklist_items=request.mandatory_checklist_items,
            default_risk_percent=request.default_risk_percent,
            max_risk_percent=request.max_risk_percent,
            metadata=request.metadata,
        )
        return {"strategy": api_registry.strategy_repository.save_strategy(strategy)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{strategy_name}/checklist")
def append_checklist(strategy_name: str, request: AppendChecklistRequest):
    try:
        updated = api_registry.strategy_repository.append_checklist_items(
            strategy_name=strategy_name,
            checklist_items=request.checklist_items,
            mandatory_items=request.mandatory_checklist_items,
        )
        return {"strategy": updated}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
