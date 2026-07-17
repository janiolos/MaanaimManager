"""Middleware de inatividade - invalida o access token após N segundos sem atividade.

Estratégia: renova o claim last_activity no access token emitido por /auth/login e /auth/refresh.
Como JWT é stateless, esta middleware valida o tempo desde a última atividade registada
no payload e devolve 401 quando expirou (cliente deve refazer login ou usar /auth/refresh).

Para manter-se stateless exigimos que o cliente envie um header X-Activity-Ping
em rotas longas; em rotas normais atualiza last_activity só no refresh.
Esta versão simplificada confia no exp do access token (curta duração).
"""

from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class InactivityLogoutMiddleware(BaseHTTPMiddleware):
    """Placeholder - a janela de inatividade é coberta pela curta vida do access token (30 min)
    somada ao refresh sliding. Em outro momento podemos implementar blocklist Redis."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        return await call_next(request)


__all__ = ["InactivityLogoutMiddleware"]