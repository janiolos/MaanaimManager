"""App FastAPI principal."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.config import settings
from app.core.routers import router as core_router
from app.finance.routers import router as finance_router
from app.inventory.routers import router as inventory_router
from app.lodging.routers import router as lodging_router
from app.pos.routers import router as pos_router
from app.middleware.audit import AuditLogMiddleware
from app.middleware.inactivity import InactivityLogoutMiddleware

logger = logging.getLogger("maanaim")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Backend Maanaim Manager - FastAPI",
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
        openapi_url="/openapi.json" if settings.is_dev else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Evento-Id"],
    )
    app.add_middleware(InactivityLogoutMiddleware)
    app.add_middleware(AuditLogMiddleware)

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(core_router, prefix="/api/v1")
    app.include_router(finance_router, prefix="/api/v1")
    app.include_router(inventory_router, prefix="/api/v1")
    app.include_router(lodging_router, prefix="/api/v1")
    app.include_router(pos_router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "project": settings.PROJECT_NAME, "environment": settings.ENVIRONMENT}

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"name": settings.PROJECT_NAME, "docs": "/docs"}

    return app


app = create_app()