from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.server.api_registry import api_registry
from api.server.auth_service import AuthServiceError

logger = logging.getLogger(__name__)


PUBLIC_PATH_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth",
    "/api/v1/share-export/shared/",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if any(path == prefix or path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        token = auth_header.split(" ", 1)[1].strip()
        try:
            auth_context = api_registry.auth_service.authenticate_token(token)
        except AuthServiceError as exc:
            # Authentication-specific errors (invalid token, expired session, etc.)
            return JSONResponse(status_code=401, content={"detail": str(exc)})
        except Exception as exc:
            # System errors (database issues, network problems, etc.)
            # Log the actual error for debugging but return a generic message
            logger.error(f"Authentication system error: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500, 
                content={"detail": "Internal authentication error"}
            )

        request.state.auth_context = auth_context
        return await call_next(request)


def get_current_user(request: Request) -> Dict[str, Any]:
    auth_context = getattr(request.state, "auth_context", None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Authentication required")
    return auth_context["user"]


def get_current_session(request: Request) -> Dict[str, Any]:
    auth_context = getattr(request.state, "auth_context", None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Authentication required")
    return auth_context["session"]


def ensure_account_access(user: Dict[str, Any], account_id: str) -> None:
    if not api_registry.auth_service.has_account_access(user, account_id):
        raise HTTPException(status_code=403, detail="Account access denied")


def ensure_trade_access(user: Dict[str, Any], trade_id: str) -> None:
    trade = api_registry.trade_repository.get_trade(trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    ensure_account_access(user, trade.to_dict().get("account_id"))


def ensure_tag_access(user: Dict[str, Any], tag_id: str) -> None:
    tag = api_registry.tag_repository.get(tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    ensure_account_access(user, tag.account_id)


def ensure_share_record_access(user: Dict[str, Any], record_id: str) -> None:
    record = api_registry.export_repository.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Share/export record not found")
    ensure_account_access(user, record.account_id)


def ensure_capture_request_access(user: Dict[str, Any], request_id: str) -> None:
    request = api_registry.screenshot_capture_repository.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Capture request not found")
    ensure_account_access(user, request.account_id)


def ensure_admin(user: Dict[str, Any]) -> None:
    if not api_registry.auth_service.is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")


def extract_payload_account_id(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    account_id = payload.get("account_id")
    return account_id if isinstance(account_id, str) and account_id else None
