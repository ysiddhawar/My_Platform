from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user
from models.journal_view import JournalFilterPreset, JournalViewConfig


router = APIRouter(prefix="/journal-views", tags=["journal-views"])


class FilterPresetPayload(BaseModel):
    name: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    visible_columns: List[str] = Field(default_factory=list)
    sort_by: Optional[str] = None
    sort_direction: str = "desc"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateJournalViewRequest(BaseModel):
    account_id: str
    default_columns: List[str] = Field(default_factory=list)
    saved_filters: List[FilterPresetPayload] = Field(default_factory=list)
    search_fields: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    view_name: Optional[str] = None


@router.post("")
def create_journal_view(request: CreateJournalViewRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        view = JournalViewConfig(
            account_id=request.account_id,
            default_columns=request.default_columns,
            saved_filters=[JournalFilterPreset.from_dict(item.model_dump()) for item in request.saved_filters],
            search_fields=request.search_fields,
            metadata=request.metadata,
        )
        api_registry.journal_view_repository.save(view, view_name=request.view_name)
        return {"journal_view": view.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_journal_views(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "journal_views": [
                view.to_dict()
                for view in api_registry.journal_view_repository.get_by_account(account_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
