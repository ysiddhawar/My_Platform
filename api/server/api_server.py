from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.server.api_registry import api_registry
from api.server.api_router import api_router
from api.server.security import AuthenticationMiddleware


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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.add_middleware(AuthenticationMiddleware)
app.include_router(api_router)
