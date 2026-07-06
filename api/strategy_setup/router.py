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


class UpdateStrategyRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    market_types: Optional[List[str]] = None
    checklist_items: Optional[List[str]] = None
    mandatory_checklist_items: Optional[List[str]] = None
    default_risk_percent: Optional[float] = None
    max_risk_percent: Optional[float] = None


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


@router.put("/{strategy_name}")
def update_strategy(strategy_name: str, request: UpdateStrategyRequest):
    try:
        existing = api_registry.strategy_repository.get_strategy(strategy_name)
        if not existing:
            raise HTTPException(status_code=404, detail="Strategy not found")

        strategy = Strategy(
            name=request.name if request.name is not None else existing["name"],
            description=request.description if request.description is not None else existing.get("description", ""),
            market_types=request.market_types if request.market_types is not None else existing.get("market_types", []),
            checklist_items=request.checklist_items if request.checklist_items is not None else existing.get("checklist_items", []),
            mandatory_checklist_items=request.mandatory_checklist_items if request.mandatory_checklist_items is not None else existing.get("mandatory_checklist_items", []),
            default_risk_percent=request.default_risk_percent if request.default_risk_percent is not None else existing.get("default_risk_percent", 1.0),
            max_risk_percent=request.max_risk_percent if request.max_risk_percent is not None else existing.get("max_risk_percent", 2.0),
            is_active=existing.get("is_active", True),
            metadata={"strategy_id": existing.get("strategy_id", ""), **existing.get("metadata", {})},
        )
        result = api_registry.strategy_repository.update_strategy(strategy)
        return {"strategy": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{strategy_name}")
def delete_strategy(strategy_name: str):
    try:
        api_registry.strategy_repository.delete_strategy(strategy_name)
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
