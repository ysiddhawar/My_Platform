from __future__ import annotations

import os
import logging
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limit configuration sourced from environment variables
# ---------------------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is not None:
        try:
            return int(raw)
        except (ValueError, TypeError):
            logger.warning("Invalid %s value '%s', falling back to %s", name, raw, default)
    return default


class InMemoryBucket:
    """Sliding-window in-memory rate limit bucket per client key."""

    __slots__ = ("_max_requests", "_window_seconds", "_buckets")

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: Dict[str, Tuple[float, int]] = {}

    def is_allowed(self, key: str) -> bool:
        import time
        now = time.monotonic()
        window_start, count = self._buckets.get(key, (now, 0))

        if now - window_start > self._window_seconds:
            window_start = now
            count = 0

        count += 1
        self._buckets[key] = (window_start, count)

        return count <= self._max_requests

    def remaining(self, key: str) -> int:
        import time
        now = time.monotonic()
        window_start, count = self._buckets.get(key, (now, 0))
        if now - window_start > self._window_seconds:
            return self._max_requests
        return max(0, self._max_requests - count)


# ---------------------------------------------------------------------------
# Rate limit presets per path prefix
# ---------------------------------------------------------------------------

# Format: (path_prefix, max_requests, window_seconds)
RATE_LIMITS: Tuple[Tuple[str, int, int], ...] = (
    # Auth endpoints – strict to prevent brute-force
    ("/api/v1/auth", _env_int("RATE_LIMIT_AUTH_MAX", 10), _env_int("RATE_LIMIT_AUTH_WINDOW", 60)),

    # Trade ingestion – moderate
    ("/api/v1/trade-ingestion", _env_int("RATE_LIMIT_TRADE_INGESTION_MAX", 60), _env_int("RATE_LIMIT_TRADE_INGESTION_WINDOW", 60)),

    # Metric computation – moderate
    ("/api/v1/metrics", _env_int("RATE_LIMIT_METRICS_MAX", 30), _env_int("RATE_LIMIT_METRICS_WINDOW", 60)),

    # AI diagnostic – expensive, stricter
    ("/api/v1/ai-diagnostic", _env_int("RATE_LIMIT_AI_DIAGNOSTIC_MAX", 15), _env_int("RATE_LIMIT_AI_DIAGNOSTIC_WINDOW", 60)),
    ("/api/v1/ai-insights", _env_int("RATE_LIMIT_AI_INSIGHTS_MAX", 20), _env_int("RATE_LIMIT_AI_INSIGHTS_WINDOW", 60)),

    # Decision engine
    ("/api/v1/decisions", _env_int("RATE_LIMIT_DECISIONS_MAX", 20), _env_int("RATE_LIMIT_DECISIONS_WINDOW", 60)),

    # Execution tools (position sizing, trade execution)
    ("/api/v1/execution-tools", _env_int("RATE_LIMIT_EXECUTION_MAX", 30), _env_int("RATE_LIMIT_EXECUTION_WINDOW", 60)),

    # Risk modeling – expensive
    ("/api/v1/risk-modeling", _env_int("RATE_LIMIT_RISK_MODELING_MAX", 15), _env_int("RATE_LIMIT_RISK_MODELING_WINDOW", 60)),

    # Recovery
    ("/api/v1/recovery", _env_int("RATE_LIMIT_RECOVERY_MAX", 10), _env_int("RATE_LIMIT_RECOVERY_WINDOW", 60)),

    # Monitoring – frequent polls allowed
    ("/api/v1/monitoring", _env_int("RATE_LIMIT_MONITORING_MAX", 120), _env_int("RATE_LIMIT_MONITORING_WINDOW", 60)),

    # Journal / notes / tags / ratings – moderate
    ("/api/v1/journal", _env_int("RATE_LIMIT_JOURNAL_MAX", 60), _env_int("RATE_LIMIT_JOURNAL_WINDOW", 60)),
    ("/api/v1/notes", _env_int("RATE_LIMIT_NOTES_MAX", 60), _env_int("RATE_LIMIT_NOTES_WINDOW", 60)),
    ("/api/v1/tags", _env_int("RATE_LIMIT_TAGS_MAX", 60), _env_int("RATE_LIMIT_TAGS_WINDOW", 60)),
    ("/api/v1/ratings", _env_int("RATE_LIMIT_RATINGS_MAX", 60), _env_int("RATE_LIMIT_RATINGS_WINDOW", 60)),

    # Attachments
    ("/api/v1/attachments", _env_int("RATE_LIMIT_ATTACHMENTS_MAX", 30), _env_int("RATE_LIMIT_ATTACHMENTS_WINDOW", 60)),

    # Dashboard / calendar / sessions / missed-ops – moderate
    ("/api/v1/dashboard", _env_int("RATE_LIMIT_DASHBOARD_MAX", 60), _env_int("RATE_LIMIT_DASHBOARD_WINDOW", 60)),
    ("/api/v1/calendar", _env_int("RATE_LIMIT_CALENDAR_MAX", 60), _env_int("RATE_LIMIT_CALENDAR_WINDOW", 60)),
    ("/api/v1/trading-sessions", _env_int("RATE_LIMIT_SESSIONS_MAX", 60), _env_int("RATE_LIMIT_SESSIONS_WINDOW", 60)),
    ("/api/v1/missed-opportunities", _env_int("RATE_LIMIT_MISSED_OPS_MAX", 30), _env_int("RATE_LIMIT_MISSED_OPS_WINDOW", 60)),

    # Share / export
    ("/api/v1/share-export", _env_int("RATE_LIMIT_EXPORT_MAX", 30), _env_int("RATE_LIMIT_EXPORT_WINDOW", 60)),

    # Governance config
    ("/api/v1/governance-config", _env_int("RATE_LIMIT_GOVERNANCE_MAX", 20), _env_int("RATE_LIMIT_GOVERNANCE_WINDOW", 60)),

    # Strategy setup
    ("/api/v1/strategy-setup", _env_int("RATE_LIMIT_STRATEGY_MAX", 30), _env_int("RATE_LIMIT_STRATEGY_WINDOW", 60)),

    # General accounts
    ("/api/v1/accounts", _env_int("RATE_LIMIT_ACCOUNTS_MAX", 30), _env_int("RATE_LIMIT_ACCOUNTS_WINDOW", 60)),

    # Visualization
    ("/api/v1/visualization", _env_int("RATE_LIMIT_VISUALIZATION_MAX", 30), _env_int("RATE_LIMIT_VISUALIZATION_WINDOW", 60)),

    # Journal views
    ("/api/v1/journal-views", _env_int("RATE_LIMIT_JOURNAL_VIEWS_MAX", 60), _env_int("RATE_LIMIT_JOURNAL_VIEWS_WINDOW", 60)),

    # Dashboard layouts
    ("/api/v1/dashboard-layouts", _env_int("RATE_LIMIT_DASHBOARD_LAYOUTS_MAX", 60), _env_int("RATE_LIMIT_DASHBOARD_LAYOUTS_WINDOW", 60)),

    # Prototype endpoints (used by frontend) – generous
    ("/api/v1/prototype", _env_int("RATE_LIMIT_PROTOTYPE_MAX", 120), _env_int("RATE_LIMIT_PROTOTYPE_WINDOW", 60)),
)

# Default fallback for any unmatched path
DEFAULT_MAX_REQUESTS = _env_int("RATE_LIMIT_DEFAULT_MAX", 60)
DEFAULT_WINDOW_SECONDS = _env_int("RATE_LIMIT_DEFAULT_WINDOW", 60)

VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Rate limit buckets (built once at import time)
# ---------------------------------------------------------------------------

_limit_buckets = {
    prefix: InMemoryBucket(max_req, window_sec)
    for prefix, max_req, window_sec in RATE_LIMITS
}
_default_bucket = InMemoryBucket(DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS)


def _resolve_bucket(path: str) -> InMemoryBucket:
    """Return the most specific bucket for a path, or the default bucket."""
    best = _default_bucket
    best_len = 0
    for prefix, _, _ in RATE_LIMITS:
        if path.startswith(prefix) and len(prefix) > best_len:
            best = _limit_buckets[prefix]
            best_len = len(prefix)
    return best


def _rate_limit_client_key(request: Request) -> str:
    """
    Derive a rate limit key for the request.

    Uses the authenticated user ID if available, otherwise falls back
    to the client IP address. This prevents one authenticated user from
    exhausting another user's rate limit.
    """
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None:
        user = auth_context.get("user")
        if user and isinstance(user, dict):
            user_id = user.get("user_id") or user.get("id")
            if user_id:
                return f"user:{user_id}"

    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    return f"ip:{client_ip}"


# ---------------------------------------------------------------------------
# ASGI Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window in-memory rate limiting middleware.

    Applied early in the middleware stack (after CORS, before authentication)
    so that unauthenticated requests are also rate-limited.
    """

    def __init__(self, app: ASGIApp, enabled: bool = True) -> None:
        super().__init__(app)
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next):
        # Do not rate-limit health checks, docs, or OPTIONS preflight
        if not self._enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Always allow health, docs, openapi
        if path in ("/health", "/docs", "/redoc", "/openapi.json") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            return await call_next(request)

        client_key = _rate_limit_client_key(request)
        bucket = _resolve_bucket(path)

        if not bucket.is_allowed(client_key):
            remaining = bucket.remaining(client_key)
            logger.info("Rate limit exceeded for %s on %s", client_key, path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "rate_limit": {
                        "remaining": remaining,
                        "retry_after_seconds": 1,  # approximate; real sliding window
                    },
                },
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": "1",
                },
            )

        return await call_next(request)