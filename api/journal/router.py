from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_trade_access, get_current_user
from core.context import Context


router = APIRouter(prefix="/journal", tags=["journal"])


class JournalSearchRequest(BaseModel):
    account_id: str = "DEFAULT"
    filters: dict = Field(default_factory=dict)
    search_text: Optional[str] = None


class BulkEditRequest(BaseModel):
    account_id: str = "DEFAULT"
    trade_ids: List[str]
    note_text: Optional[str] = None
    note_title: str = "Bulk Update"
    tag_ids: List[str] = Field(default_factory=list)
    rating_value: Optional[float] = None
    rating_rationale: Optional[str] = None


@router.get("/trades")
def list_trades(
    account_id: str = "DEFAULT",
    closed_only: Optional[bool] = None,
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, account_id)
        trades = api_registry.trade_repository.get_trades_by_account(
            account_id=account_id,
            closed_only=closed_only,
        )
        return {"trades": [trade.to_dict() for trade in trades]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/behavior")
def behavioral_snapshot(
    account_id: str = "DEFAULT",
    lookback: Optional[int] = None,
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, account_id)
        trades = api_registry.trade_repository.get_trades_by_account(account_id=account_id)
        sessions = api_registry.trading_platform_session_repository.list_by_account(account_id)
        missed_opportunities = api_registry.missed_opportunity_repository.list_by_account(account_id)
        analysis_context = Context()
        analysis_context.set_cache("trades", trades)
        analysis_context.set_cache("trading_platform_sessions", sessions)
        analysis_context.set_cache("missed_opportunities", missed_opportunities)
        analysis = api_registry.behavioral_analyzer.analyze(
            context=analysis_context,
            lookback=lookback,
        )
        return analysis
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}")
def get_trade_detail(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        trade = api_registry.trade_repository.get_trade(trade_id)
        if trade is None:
            return {"trade": None}
        return {"trade": trade.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}/bundle")
def get_trade_bundle(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        trade = api_registry.trade_repository.get_trade(trade_id)
        if trade is None:
            return {"trade": None, "attachments": [], "notes": [], "tags": [], "rating": None}
        return {
            "trade": trade.to_dict(),
            "attachments": [
                attachment.to_dict()
                for attachment in api_registry.attachment_repository.get_by_trade(trade_id)
            ],
            "notes": [
                note.to_dict()
                for note in api_registry.note_repository.get_by_trade(trade_id)
            ],
            "tags": [
                tag.to_dict()
                for tag in api_registry.tag_repository.list_for_trade(trade_id)
            ],
            "rating": (
                api_registry.rating_repository.get_for_trade(trade_id).to_dict()
                if api_registry.rating_repository.get_for_trade(trade_id)
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/search")
def search_journal(request: JournalSearchRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return {
            "results": api_registry.journal_query_engine.query(
                account_id=request.account_id,
                filters=request.filters,
                search_text=request.search_text,
            )
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bulk-edit")
def bulk_edit_journal(request: BulkEditRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        for trade_id in request.trade_ids:
            ensure_trade_access(user, trade_id)
        return api_registry.journal_bulk_editor.apply(
            account_id=request.account_id,
            trade_ids=request.trade_ids,
            note_text=request.note_text,
            note_title=request.note_title,
            tag_ids=request.tag_ids,
            rating_value=request.rating_value,
            rating_rationale=request.rating_rationale,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
