"""Routers de autenticação - login, refresh, me, logout."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.auth.jwt import InvalidTokenError, create_access_token, create_refresh_token, decode_token
from app.auth.passwords import verify_password
from app.auth.schemas import GroupOut, LoginIn, MeOut, RefreshOut, TokenOut, UserOut
from app.core.services import UserService
from app.config import settings
from app.core.models import User
from app.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_PATH = "/auth/refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=not settings.is_dev,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_PATH)


async def _user_to_out(user: User, session: AsyncSession) -> UserOut:
    from app.core.services import UserService
    groups = [GroupOut(id=g.id, name=g.name) for g in user.groups]
    scopes = await UserService.get_scopes(session, user.id)
    return UserOut(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_superuser=user.is_superuser,
        is_staff=user.is_staff,
        groups=groups,
        scopes=scopes,
    )


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginIn,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenOut:
    stmt = select(User).where(User.username == payload.username)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    scopes = await UserService.get_scopes(session, user.id)
    access = create_access_token(
        subject=user.id,
        is_superuser=user.is_superuser,
        groups=[g.name for g in user.groups],
        scopes=scopes,
        evento_id=None,
    )
    refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh)

    return TokenOut(
        access_token=access,
        token_type="bearer",
        user=await _user_to_out(user, session),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=RefreshOut)
async def refresh(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> RefreshOut:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente")
    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token inválido") from exc
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token malformado") from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    scopes = await UserService.get_scopes(session, user.id)
    access = create_access_token(
        subject=user.id,
        is_superuser=user.is_superuser,
        groups=[g.name for g in user.groups],
        scopes=scopes,
        evento_id=None,
    )
    # rotaciona refresh token (sliding)
    new_refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, new_refresh)

    return RefreshOut(
        access_token=access,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=MeOut)
async def me(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MeOut:
    return MeOut(**(await _user_to_out(current, session)).model_dump())


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    _clear_refresh_cookie(response)
    return None