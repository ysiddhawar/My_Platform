from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, ensure_admin, ensure_capture_request_access, ensure_trade_access, get_current_user
from models.trade_attachment import AttachmentMarker, TradeAttachment


router = APIRouter(prefix="/attachments", tags=["attachments"])


class AttachmentMarkerPayload(BaseModel):
    label: str
    price: Optional[float] = None
    timestamp: Optional[str] = None
    color: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateAttachmentRequest(BaseModel):
    account_id: str
    trade_id: str
    attachment_type: str
    file_name: str
    storage_path: str
    source: str
    broker_id: Optional[str] = None
    market_type: Optional[str] = None
    content_type: Optional[str] = None
    description: Optional[str] = None
    is_auto_captured: bool = False
    markers: List[AttachmentMarkerPayload] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateCaptureRequest(BaseModel):
    trade_id: str
    requested_by: str = "system"
    trigger: str = "manual_request"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestCaptureRequest(BaseModel):
    request_id: str
    file_name: str
    storage_path: str
    source: str
    content_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FailCaptureRequest(BaseModel):
    request_id: str
    reason: str


class RegisterCaptureSourceRequest(BaseModel):
    source_name: str
    source_type: str
    account_ids: List[str] = Field(default_factory=list)
    broker_ids: List[str] = Field(default_factory=list)
    market_types: List[str] = Field(default_factory=list)
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class CaptureSourceHeartbeatRequest(BaseModel):
    source_id: str
    status: str = "active"


class ClaimCaptureRequest(BaseModel):
    source_id: str


class SubmitSourceCaptureRequest(BaseModel):
    source_id: str
    request_id: str
    file_name: str
    storage_path: str
    content_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubmitSourceCaptureBytesRequest(BaseModel):
    source_id: str
    request_id: str
    file_name: str
    content_base64: str
    storage_dir: str = "capture_uploads"
    content_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FailSourceCaptureRequest(BaseModel):
    source_id: str
    request_id: str
    reason: str


@router.post("")
def create_attachment(request: CreateAttachmentRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        ensure_trade_access(user, request.trade_id)
        attachment = TradeAttachment(
            account_id=request.account_id,
            trade_id=request.trade_id,
            attachment_type=request.attachment_type,
            file_name=request.file_name,
            storage_path=request.storage_path,
            source=request.source,
            broker_id=request.broker_id,
            market_type=request.market_type,
            content_type=request.content_type,
            description=request.description,
            is_auto_captured=request.is_auto_captured,
            markers=[AttachmentMarker(**marker.model_dump()) for marker in request.markers],
            metadata=request.metadata,
        )
        api_registry.attachment_repository.save(attachment)
        return {"attachment": attachment.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trade/{trade_id}")
def list_trade_attachments(trade_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, trade_id)
        return {
            "attachments": [
                attachment.to_dict()
                for attachment in api_registry.attachment_repository.get_by_trade(trade_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-request")
def create_capture_request(request: CreateCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_trade_access(user, request.trade_id)
        return {
            "capture_request": api_registry.screenshot_capture_service.request_for_trade(
                trade_id=request.trade_id,
                requested_by=request.requested_by,
                trigger=request.trigger,
                metadata=request.metadata,
            )
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-ingest")
def ingest_capture(request: IngestCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_capture_request_access(user, request.request_id)
        return api_registry.screenshot_capture_service.ingest_capture(
            request_id=request.request_id,
            file_name=request.file_name,
            storage_path=request.storage_path,
            source=request.source,
            content_type=request.content_type,
            description=request.description,
            metadata=request.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-fail")
def fail_capture(request: FailCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_capture_request_access(user, request.request_id)
        return {
            "capture_request": api_registry.screenshot_capture_service.mark_failed(
                request_id=request.request_id,
                reason=request.reason,
            )
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/capture-pending")
def list_pending_capture_requests(user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        return {
            "capture_requests": api_registry.screenshot_capture_service.list_pending()
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/register")
def register_capture_source(request: RegisterCaptureSourceRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        return api_registry.screenshot_source_integration_service.register_source(
            source_name=request.source_name,
            source_type=request.source_type,
            account_ids=request.account_ids,
            broker_ids=request.broker_ids,
            market_types=request.market_types,
            capabilities=request.capabilities,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/heartbeat")
def capture_source_heartbeat(request: CaptureSourceHeartbeatRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        return api_registry.screenshot_source_integration_service.heartbeat(
            source_id=request.source_id,
            status=request.status,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/capture-sources")
def list_capture_sources(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        return api_registry.screenshot_source_integration_service.list_sources(status=status)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/claim-next")
def claim_next_capture_request(request: ClaimCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        return api_registry.screenshot_source_integration_service.claim_next(
            source_id=request.source_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/submit")
def submit_capture_from_source(request: SubmitSourceCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        ensure_capture_request_access(user, request.request_id)
        return api_registry.screenshot_source_integration_service.submit_capture(
            source_id=request.source_id,
            request_id=request.request_id,
            file_name=request.file_name,
            storage_path=request.storage_path,
            content_type=request.content_type,
            description=request.description,
            metadata=request.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/submit-bytes")
def submit_capture_bytes_from_source(request: SubmitSourceCaptureBytesRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        ensure_capture_request_access(user, request.request_id)
        return api_registry.screenshot_source_integration_service.submit_capture_bytes(
            source_id=request.source_id,
            request_id=request.request_id,
            file_name=request.file_name,
            content_base64=request.content_base64,
            storage_dir=request.storage_dir,
            content_type=request.content_type,
            description=request.description,
            metadata=request.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/capture-sources/fail")
def fail_capture_from_source(request: FailSourceCaptureRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        ensure_capture_request_access(user, request.request_id)
        return api_registry.screenshot_source_integration_service.fail_capture(
            source_id=request.source_id,
            request_id=request.request_id,
            reason=request.reason,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
