from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_trade_access, get_current_user
from models.journal_note import JournalNote


router = APIRouter(prefix="/notes", tags=["notes"])


class CreateNoteRequest(BaseModel):
    account_id: str
    note_type: str
    title: str
    body: str
    trade_id: Optional[str] = None
    note_date: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("")
def create_note(request: CreateNoteRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        if request.trade_id:
            ensure_trade_access(user, request.trade_id)
        note = JournalNote(**request.model_dump())
        api_registry.note_repository.save(note)
        return {"note": note.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_notes(account_id: str, note_type: Optional[str] = None, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "notes": [
                note.to_dict()
                for note in api_registry.note_repository.get_by_account(account_id, note_type=note_type)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}")
def list_trade_notes(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        return {"notes": [note.to_dict() for note in api_registry.note_repository.get_by_trade(trade_id)]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
