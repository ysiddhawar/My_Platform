from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_share_record_access, get_current_user
from models.share_export_record import ShareExportRecord


router = APIRouter(prefix="/share-export", tags=["share-export"])


class CreateShareExportRequest(BaseModel):
    account_id: str
    record_type: str
    target_type: str
    target_id: str
    format: str
    status: str
    storage_path: Optional[str] = None
    share_token: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateShareLinkRequest(BaseModel):
    account_id: str
    target_type: str
    target_id: str
    expires_in_hours: int = 168
    include_notes: bool = True
    include_attachments: bool = True


class RevokeShareLinkRequest(BaseModel):
    record_id: str


@router.post("")
def create_share_export(request: CreateShareExportRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        record = ShareExportRecord(**request.model_dump())
        api_registry.export_repository.save(record)
        return {"share_export": record.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_share_exports(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "share_exports": [
                record.to_dict()
                for record in api_registry.export_repository.get_by_account(account_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate")
def generate_export(account_id: str, export_format: str = "json", output_dir: str = "exports", user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return api_registry.export_service.generate_account_export(
            account_id=account_id,
            export_format=export_format,
            output_dir=output_dir,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/share-link")
def create_share_link(request: CreateShareLinkRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        return api_registry.share_link_service.create_share_link(
            account_id=request.account_id,
            target_type=request.target_type,
            target_id=request.target_id,
            expires_in_hours=request.expires_in_hours,
            include_notes=request.include_notes,
            include_attachments=request.include_attachments,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/shared-links")
def list_share_links(account_id: str, target_type: Optional[str] = None, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return api_registry.share_link_service.list_share_links(
            account_id=account_id,
            target_type=target_type,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/shared/{share_token}")
def resolve_share_link(share_token: str):
    try:
        return api_registry.share_link_service.resolve_share_link(share_token)
    except PermissionError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/revoke")
def revoke_share_link(request: RevokeShareLinkRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_share_record_access(user, request.record_id)
        return api_registry.share_link_service.revoke_share_link(request.record_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
