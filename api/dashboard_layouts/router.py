from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import ensure_account_access, get_current_user
from models.dashboard_layout import DashboardLayout, DashboardWidget


router = APIRouter(prefix="/dashboard-layouts", tags=["dashboard-layouts"])


class DashboardWidgetPayload(BaseModel):
    widget_key: str
    title: str
    position: Dict[str, int]
    config: Dict[str, Any] = Field(default_factory=dict)


class CreateDashboardLayoutRequest(BaseModel):
    account_id: str
    dashboard_name: str
    template_name: Optional[str] = None
    widgets: List[DashboardWidgetPayload] = Field(default_factory=list)
    theme_overrides: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpsertWorkspaceLayoutRequest(BaseModel):
    account_id: str
    dashboard_name: str = "web_app_workspace"
    widgets: List[DashboardWidgetPayload] = Field(default_factory=list)
    theme_overrides: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("")
def create_dashboard_layout(request: CreateDashboardLayoutRequest, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, request.account_id)
        layout = DashboardLayout(
            account_id=request.account_id,
            dashboard_name=request.dashboard_name,
            template_name=request.template_name,
            widgets=[DashboardWidget.from_dict(item.model_dump()) for item in request.widgets],
            theme_overrides=request.theme_overrides,
            metadata=request.metadata,
        )
        api_registry.dashboard_repository.save(layout)
        return {"dashboard_layout": layout.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_dashboard_layouts(account_id: str, user: dict = Depends(get_current_user)):
    try:
        ensure_account_access(user, account_id)
        return {
            "dashboard_layouts": [
                layout.to_dict()
                for layout in api_registry.dashboard_repository.get_by_account(account_id)
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/current")
def get_current_workspace_layout(
    account_id: str,
    dashboard_name: str = "web_app_workspace",
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, account_id)
        layouts = api_registry.dashboard_repository.get_by_account(account_id)
        layout = next((item for item in layouts if item.dashboard_name == dashboard_name), None)
        return {"dashboard_layout": layout.to_dict() if layout else None}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/current")
def upsert_current_workspace_layout(
    request: UpsertWorkspaceLayoutRequest,
    user: dict = Depends(get_current_user),
):
    try:
        ensure_account_access(user, request.account_id)
        layouts = api_registry.dashboard_repository.get_by_account(request.account_id)
        existing = next((item for item in layouts if item.dashboard_name == request.dashboard_name), None)

        if existing is None:
            layout = DashboardLayout(
                account_id=request.account_id,
                dashboard_name=request.dashboard_name,
                widgets=[DashboardWidget.from_dict(item.model_dump()) for item in request.widgets],
                theme_overrides=request.theme_overrides,
                metadata=request.metadata,
            )
        else:
            layout = replace(
                existing,
                widgets=[DashboardWidget.from_dict(item.model_dump()) for item in request.widgets],
                theme_overrides=request.theme_overrides,
                metadata=request.metadata,
                updated_at=datetime.now(timezone.utc),
            )

        api_registry.dashboard_repository.save(layout)
        return {"dashboard_layout": layout.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
