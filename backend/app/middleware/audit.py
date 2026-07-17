"""Middleware de auditoria - registra cada request em core_auditlog."""

from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import async_session_factory


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # não autentica aqui - só registra metadados pós-response
        response = await call_next(request)

        # ignora assets/docs/dev tools
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            return response
        if path.startswith("/static") or path.startswith("/media"):
            return response

        try:
            async with async_session_factory() as session:
                from app.core.models import AuditLog
                from sqlalchemy import select
                from app.core.models import User

                user_id: int | None = None
                auth = request.headers.get("Authorization", "")
                if auth.lower().startswith("bearer "):
                    try:
                        from app.auth.jwt import decode_token, InvalidTokenError
                        payload = decode_token(auth[7:])
                        if payload.get("type") == "access":
                            user_id = int(payload.get("sub", 0)) or None
                    except (InvalidTokenError, ValueError):
                        pass

                view_name = ""
                if hasattr(request, "scope") and "route" in request.scope:
                    route = request.scope.get("route")
                    if hasattr(route, "name"):
                        view_name = route.name or ""

                record = AuditLog(
                    user_id=user_id,
                    method=request.method,
                    path=path,
                    view_name=view_name,
                    status_code=response.status_code,
                    ip_address=_client_ip(request),
                    user_agent=request.headers.get("user-agent", "")[:2048],
                )
                session.add(record)
                await session.commit()
        except Exception:  # nunca derrubar request
            pass

        return response