from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.server.api_registry import api_registry
from api.server.security import ensure_admin, get_current_user


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MonitoringEventRequest(BaseModel):
    event: Dict[str, Any]


class AuditLogRequest(BaseModel):
    category: str
    component: str
    event_type: str
    details: Dict[str, Any] = {}
    severity: str = "info"
    metadata: Dict[str, Any] = {}


class GenericStatusResponse(BaseModel):
    status: str
    data: Dict[str, Any]


@router.post("/anomaly", response_model=GenericStatusResponse)
def record_anomaly(request: MonitoringEventRequest, user: dict = Depends(get_current_user)):
    ensure_admin(user)
    api_registry.monitoring_registry.record_anomaly(request.event)
    return GenericStatusResponse(status="ok", data=api_registry.monitoring_registry.snapshot())


@router.post("/audit-log", response_model=GenericStatusResponse)
def create_audit_log(request: AuditLogRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_admin(user)
        log_id = api_registry.audit_logger.log_event(
            category=request.category,
            component=request.component,
            event_type=request.event_type,
            details=request.details,
            severity=request.severity,
            metadata=request.metadata,
        )
        return GenericStatusResponse(status="ok", data={"log_id": log_id})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/snapshot", response_model=GenericStatusResponse)
def monitoring_snapshot(user: dict = Depends(get_current_user)):
    ensure_admin(user)
    data = {
        "monitoring_registry": api_registry.monitoring_registry.snapshot(),
        "health_status": api_registry.health_monitor.get_status(),
        "audit_stats": api_registry.audit_logger.stats(),
    }
    return GenericStatusResponse(status="ok", data=data)
