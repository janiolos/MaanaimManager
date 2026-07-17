"""Dependencies FastAPI para auth/scopes/evento atual."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import InvalidTokenError, decode_token
from app.auth.scopes import groups_to_scopes
from app.core.models import User
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inesperado")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token sem subject")
    try:
        user_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="subject inválido") from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário inexistente ou inativo")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_scopes(*required: str):
    """Dependency factory: garante que o usuário possui todos os scopes listados.

    Superuser bypassa (já vem com scopes administrativos no JWT).
    """

    async def _checker(
        user: CurrentUser,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    ) -> User:
        scopes: list[str] = []
        if credentials is not None:
            try:
                payload = decode_token(credentials.credentials)
                scopes = payload.get("scopes", [])
            except InvalidTokenError:
                scopes = []
        if user.is_superuser:
            return user
        missing = set(required) - set(scopes)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scopes insuficientes: faltando {sorted(missing)}",
            )
        return user

    return _checker


async def get_evento_atual_id(
    x_evento_id: Annotated[int | None, Header(alias="X-Evento-Id")] = None,
) -> int | None:
    """Lê o header X-Evento-Id enviado pelo frontend a cada request."""
    return x_evento_id


EventoAtualId = Annotated[int | None, Depends(get_evento_atual_id)]


async def require_admin_or_responsavel(
    evento_id: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    from app.core.models import Evento

    evento = await session.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    if user.is_superuser:
        return user
    if evento.responsavel_geral_id == user.id:
        return user

    from app.core.services import UserService
    scopes = await UserService.get_scopes(session, user.id)
    if "admin:write" in scopes or "core:write" in scopes:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado: requer admin ou responsável pelo evento",
    )