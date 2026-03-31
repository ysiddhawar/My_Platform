from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.server.api_registry import api_registry
from api.server.security import get_current_user
from models.account import Account


router = APIRouter(prefix="/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    account_id: str | None = None
    broker_id: str
    account_name: str
    initial_balance: float = Field(default=100000.0, gt=0)
    risk_level: str = "survival"
    base_currency: str = "USD"
    supported_market_types: list[str] = Field(default_factory=lambda: ["stock", "forex", "crypto", "futures"])
    timezone_name: str = "UTC"
    auto_connect_simulated: bool = True


class ConnectSimulatedRequest(BaseModel):
    broker_id: str | None = None


class ConnectMt5FileBridgeRequest(BaseModel):
    broker_id: str | None = None
    inbox_dir: str
    archive_dir: str | None = None
    poll_interval_seconds: float = Field(default=0.25, gt=0)


class ValidateMt5FileBridgeRequest(BaseModel):
    inbox_dir: str
    archive_dir: str | None = None


def _directory_state(path_value: str):
    path = Path(path_value).expanduser()
    return {
        "path": str(path),
        "exists": path.exists(),
        "writable": os.access(path if path.exists() else path.parent, os.W_OK),
    }


def _validate_directory_access(path_value: str) -> tuple[bool, str | None]:
    path = Path(path_value).expanduser()
    if path.exists() and not path.is_dir():
        return False, f"{path} exists but is not a directory."
    probe_dir = path if path.exists() else path.parent
    if not probe_dir.exists():
        return False, f"{probe_dir} does not exist yet, so the platform cannot create {path.name} there."
    return True, None


@router.get("")
def list_accounts(user: dict = Depends(get_current_user)):
    try:
        all_accounts = api_registry.account_repository.get_all_accounts()
        roles = set(user.get("roles", []))
        allowed_accounts = set(user.get("account_ids", []))

        if "admin" in roles or "*" in allowed_accounts:
            visible = all_accounts
        else:
            visible = [account for account in all_accounts if account.to_dict().get("account_id") in allowed_accounts]

        return {
            "accounts": [
                {
                    "account_id": payload["account_id"],
                    "account_name": payload.get("account_name"),
                    "broker_id": payload.get("broker_id"),
                    "base_currency": payload.get("base_currency"),
                    "risk_level": payload.get("risk_level"),
                    "supported_market_types": payload.get("supported_market_types", []),
                    "is_active": payload.get("is_active", True),
                }
                for payload in [account.to_dict() for account in visible]
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("")
def create_account(request: CreateAccountRequest, user: dict = Depends(get_current_user)):
    try:
        account = Account(
            broker_id=request.broker_id,
            account_name=request.account_name,
            initial_balance=request.initial_balance,
            risk_level=request.risk_level,
            base_currency=request.base_currency,
            supported_market_types=request.supported_market_types,
            metadata={"timezone_name": request.timezone_name, "created_via": "web_app"},
        )
        if request.account_id:
            account._account_id = request.account_id
        api_registry.account_repository.save(account)

        # Persist access for non-admin users so the newly created account is immediately visible.
        if "admin" not in set(user.get("roles", [])) and "*" not in set(user.get("account_ids", [])):
            existing_user = api_registry.user_repository.get(user["user_id"])
            if existing_user is not None and account.account_id not in existing_user.account_ids:
                updated_user = replace(
                    existing_user,
                    account_ids=[*existing_user.account_ids, account.account_id],
                    updated_at=datetime.now(timezone.utc),
                )
                api_registry.user_repository.save(updated_user)

        integration = None
        if request.auto_connect_simulated:
            integration = api_registry.broker_integration_service.register_simulated_adapter(
                account_id=account.account_id,
                broker_id=request.broker_id,
            )

        return {
            "account": account.to_dict(),
            "integration": integration,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/integrations")
def list_integrations(user: dict = Depends(get_current_user)):
    try:
        payload = api_registry.broker_integration_service.list_integrations()
        allowed_accounts = set(user.get("account_ids", []))
        roles = set(user.get("roles", []))
        if "admin" in roles or "*" in allowed_accounts:
            return payload
        return {
            "integrations": [
                item for item in payload.get("integrations", []) if item.get("account_id") in allowed_accounts
            ]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mt5-file-bridge/validate")
def validate_mt5_file_bridge(request: ValidateMt5FileBridgeRequest, user: dict = Depends(get_current_user)):
    try:
        inbox_path = Path(request.inbox_dir).expanduser()
        archive_path = Path(request.archive_dir).expanduser() if request.archive_dir else inbox_path / "processed"

        warnings: list[str] = []
        instructions = [
            "Point your MT5 bridge or EA export directory at the inbox path shown below.",
            "Write one JSON file per event into the inbox directory.",
            "Keep the archive directory separate from the live inbox to avoid duplicate ingestion.",
            "Use the same broker and account mapping in MT5 and in MyPlatform.",
        ]

        inbox_ok, inbox_error = _validate_directory_access(str(inbox_path))
        archive_ok, archive_error = _validate_directory_access(str(archive_path))

        if inbox_path == archive_path:
            warnings.append("Inbox and archive paths are the same. Use a separate archive directory to avoid reprocessing.")
        if not request.archive_dir:
            warnings.append("Archive directory not supplied. MyPlatform will default to an inbox/processed folder.")

        problems = [message for message in [inbox_error, archive_error] if message]
        return {
            "ok": inbox_ok and archive_ok and not problems,
            "inbox_dir": str(inbox_path),
            "archive_dir": str(archive_path),
            "inbox_exists": inbox_path.exists(),
            "archive_exists": archive_path.exists(),
            "inbox_writable": os.access(inbox_path if inbox_path.exists() else inbox_path.parent, os.W_OK),
            "archive_writable": os.access(archive_path if archive_path.exists() else archive_path.parent, os.W_OK),
            "warnings": warnings + problems,
            "instructions": instructions,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{account_id}/connect-simulated")
def connect_simulated_account(
    account_id: str,
    request: ConnectSimulatedRequest,
    user: dict = Depends(get_current_user),
):
    try:
        account = api_registry.account_repository.get(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        if "admin" not in set(user.get("roles", [])) and "*" not in set(user.get("account_ids", [])) and account_id not in set(user.get("account_ids", [])):
            raise HTTPException(status_code=403, detail="Account access denied")
        return api_registry.broker_integration_service.register_simulated_adapter(
            account_id=account_id,
            broker_id=request.broker_id or account.broker_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{account_id}/connect-mt5-file-bridge")
def connect_mt5_file_bridge(
    account_id: str,
    request: ConnectMt5FileBridgeRequest,
    user: dict = Depends(get_current_user),
):
    try:
        account = api_registry.account_repository.get(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        if "admin" not in set(user.get("roles", [])) and "*" not in set(user.get("account_ids", [])) and account_id not in set(user.get("account_ids", [])):
            raise HTTPException(status_code=403, detail="Account access denied")
        return api_registry.broker_integration_service.register_mt5_file_bridge(
            account_id=account_id,
            broker_id=request.broker_id or account.broker_id,
            inbox_dir=request.inbox_dir,
            archive_dir=request.archive_dir,
            poll_interval_seconds=request.poll_interval_seconds,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{account_id}/disconnect")
def disconnect_account(account_id: str, user: dict = Depends(get_current_user)):
    try:
        if "admin" not in set(user.get("roles", [])) and "*" not in set(user.get("account_ids", [])) and account_id not in set(user.get("account_ids", [])):
            raise HTTPException(status_code=403, detail="Account access denied")
        return api_registry.broker_integration_service.disconnect_account(account_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
