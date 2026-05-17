from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.server.api_registry import api_registry
from api.server.api_router import api_router
from api.server.security import AuthenticationMiddleware
from api.server.rate_limiter import RateLimitMiddleware


def _parse_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_registry.startup()
    try:
        yield
    finally:
        api_registry.close()


app = FastAPI(
    title="My_Platform API",
    version="1.0.0",
    description="Thin API interface over My_Platform internal modules.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting is applied after CORS but before authentication
# so that unauthenticated paths (auth endpoints, health) are also protected.
app.add_middleware(RateLimitMiddleware)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.add_middleware(AuthenticationMiddleware)
app.include_router(api_router)
