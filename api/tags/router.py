from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_tag_access, ensure_trade_access, get_current_user
from models.trade_tag import TradeTag


router = APIRouter(prefix="/tags", tags=["tags"])


class CreateTagRequest(BaseModel):
    account_id: str
    name: str
    category: str
    color: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssignTagRequest(BaseModel):
    account_id: str
    trade_id: str
    tag_id: str


class SeedTaxonomyRequest(BaseModel):
    account_id: str
    categories: list[str] = Field(default_factory=list)
    overwrite_existing: bool = False


class UpsertTaxonomyTagRequest(BaseModel):
    account_id: str
    name: str
    category: str
    color: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tag_id: Optional[str] = None


class DeleteTagRequest(BaseModel):
    tag_id: str


@router.post("")
def create_tag(request: CreateTagRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        tag = TradeTag(**request.model_dump())
        api_registry.tag_repository.save(tag)
        return {"tag": tag.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assign")
def assign_tag(request: AssignTagRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        ensure_trade_access(user, request.trade_id)
        api_registry.tag_repository.assign_to_trade(
            account_id=request.account_id,
            trade_id=request.trade_id,
            tag_id=request.tag_id,
            linked_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"status": "assigned"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_tags(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {"tags": [tag.to_dict() for tag in api_registry.tag_repository.list_by_account(account_id)]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}")
def list_trade_tags(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        return {"tags": [tag.to_dict() for tag in api_registry.tag_repository.list_for_trade(trade_id)]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/taxonomy/summary")
def taxonomy_summary(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return api_registry.tag_taxonomy_service.taxonomy_summary(account_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/taxonomy/category/{category}")
def taxonomy_category(account_id: str, category: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return api_registry.tag_taxonomy_service.list_by_category(account_id, category)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/taxonomy/seed")
def seed_taxonomy(request: SeedTaxonomyRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.tag_taxonomy_service.seed_presets(
            account_id=request.account_id,
            categories=request.categories,
            overwrite_existing=request.overwrite_existing,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/taxonomy/upsert")
def upsert_taxonomy_tag(request: UpsertTaxonomyTagRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.tag_taxonomy_service.upsert_tag(
            account_id=request.account_id,
            name=request.name,
            category=request.category,
            color=request.color,
            description=request.description,
            metadata=request.metadata,
            tag_id=request.tag_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/taxonomy/delete")
def delete_taxonomy_tag(request: DeleteTagRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_tag_access(user, request.tag_id)
        return api_registry.tag_taxonomy_service.delete_tag(request.tag_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
