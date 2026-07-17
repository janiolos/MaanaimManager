"""Routers do módulo core - eventos, configuração, dashboard."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, EventoAtualId, require_admin_or_responsavel, require_scopes
from app.core import schemas, services
from app.core.models import Evento
from app.core.schemas import (
    AuditLogOut,
    ConfiguracaoEventoOut,
    ConfiguracaoEventoUpdate,
    ConfiguracaoSistemaOut,
    ConfiguracaoSistemaUpdate,
    EventoCreate,
    EventoOut,
    EventoUpdate,
    CentroCustoOut,
    CentroCustoCreate,
    CentroCustoUpdate,
    PaginatedAuditLogs,
    PasswordResetPayload,
    PermissionOut,
    RoleOut,
    RoleSimpleOut,
    UserSimpleOut,
    UserOut,
    UserCreate,
    UserUpdate,
    GroupOut,
    UserPermissionsOut,
)
from app.db.session import get_session

router = APIRouter(prefix="/core", tags=["core"])


@router.get("/eventos", response_model=list[EventoOut])
async def eventos_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    apenas_ativos: bool = True,
) -> list[EventoOut]:
    if apenas_ativos:
        events = await services.EventoService.list_ativos(session)
    else:
        from sqlalchemy import select
        from app.core.models import Evento
        stmt = select(Evento).order_by(Evento.data_inicio.desc())
        events = (await session.execute(stmt)).scalars().all()
    return [EventoOut.model_validate(e) for e in events]


@router.post("/eventos", response_model=EventoOut, status_code=201)
async def evento_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("core:write"))],
    payload: EventoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventoOut:
    evento = await services.EventoService.create(session, payload)
    return EventoOut.model_validate(evento)


@router.get("/eventos/{evento_id}", response_model=EventoOut)
async def evento_detalhe(
    current: CurrentUser,
    evento_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventoOut:
    try:
        evento = await services.EventoService.get(session, evento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Evento não encontrado") from exc
    return EventoOut.model_validate(evento)


@router.patch("/eventos/{evento_id}", response_model=EventoOut)
async def evento_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("core:write"))],
    evento_id: int,
    payload: EventoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventoOut:
    try:
        evento = await services.EventoService.get(session, evento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Evento não encontrado") from exc
    await services.EventoService.update(session, evento, payload)
    return EventoOut.model_validate(evento)


@router.get("/configuracao", response_model=ConfiguracaoSistemaOut)
async def configuracao(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConfiguracaoSistemaOut:
    config = await services.ConfiguracaoService.get_solo(session)
    return ConfiguracaoSistemaOut.model_validate(config)


@router.patch("/configuracao", response_model=ConfiguracaoSistemaOut)
async def configuracao_atualizar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    payload: ConfiguracaoSistemaUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConfiguracaoSistemaOut:
    config = await services.ConfiguracaoService.get_solo(session)
    config = await services.ConfiguracaoService.update(session, config, payload.model_dump(exclude_unset=True))
    return ConfiguracaoSistemaOut.model_validate(config)


@router.get("/eventos/{evento_id}/configuracao", response_model=ConfiguracaoEventoOut)
async def evento_configuracao(
    current: CurrentUser,
    evento_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConfiguracaoEventoOut:
    await require_admin_or_responsavel(evento_id, current, session)
    config = await services.ConfiguracaoEventoService.get_or_create(session, evento_id)
    return ConfiguracaoEventoOut.model_validate(config)


@router.patch("/eventos/{evento_id}/configuracao", response_model=ConfiguracaoEventoOut)
async def evento_configuracao_atualizar(
    current: CurrentUser,
    evento_id: int,
    payload: ConfiguracaoEventoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConfiguracaoEventoOut:
    await require_admin_or_responsavel(evento_id, current, session)
    config = await services.ConfiguracaoEventoService.get_or_create(session, evento_id)
    config = await services.ConfiguracaoEventoService.update(session, config, payload.model_dump(exclude_unset=True))
    return ConfiguracaoEventoOut.model_validate(config)


@router.post("/eventos/{evento_id}/encerrar", response_model=EventoOut)
async def evento_encerrar(
    current: CurrentUser,
    evento_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventoOut:
    await require_admin_or_responsavel(evento_id, current, session)
    try:
        evento = await services.EventoService.get(session, evento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Evento não encontrado") from exc
    if evento.fechado or evento.status == Evento.ENCERRADO:
        raise HTTPException(status_code=400, detail="Evento já está encerrado")
    evento = await services.EventoService.encerrar(session, evento, current.id)
    return EventoOut.model_validate(evento)


@router.get("/evento-atual/{evento_id}", response_model=EventoOut)
async def evento_atual(
    current: CurrentUser,
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventoOut:
    """Valida o evento_id recebido no header X-Evento-Id devolve o evento completo."""
    if evento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum evento selecionado (header X-Evento-Id ausente)",
        )
    try:
        evento = await services.EventoService.get(session, evento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Evento não encontrado") from exc
    return EventoOut.model_validate(evento)


@router.get("/centros-custo", response_model=list[CentroCustoOut])
async def centros_custo_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CentroCustoOut]:
    items = await services.CentroCustoService.list_ativos(session)
    return [CentroCustoOut.model_validate(x) for x in items]


@router.post("/centros-custo", response_model=CentroCustoOut, status_code=201)
async def centros_custo_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    payload: CentroCustoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CentroCustoOut:
    cc = await services.CentroCustoService.create(session, payload.model_dump())
    return CentroCustoOut.model_validate(cc)


@router.patch("/centros-custo/{cc_id}", response_model=CentroCustoOut)
async def centros_custo_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    cc_id: int,
    payload: CentroCustoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CentroCustoOut:
    try:
        cc = await services.CentroCustoService.get(session, cc_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Centro de custo não encontrado") from exc
    cc = await services.CentroCustoService.update(session, cc, payload.model_dump(exclude_unset=True))
    return CentroCustoOut.model_validate(cc)


@router.delete("/centros-custo/{cc_id}", status_code=204)
async def centros_custo_deletar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    cc_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        cc = await services.CentroCustoService.get(session, cc_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Centro de custo não encontrado") from exc
    await services.CentroCustoService.delete(session, cc)
    return None


@router.get("/grupos", response_model=list[GroupOut])
async def grupos_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[GroupOut]:
    from sqlalchemy import select
    from app.core.models import Group
    result = await session.execute(select(Group).order_by(Group.name))
    return [GroupOut.model_validate(x) for x in result.scalars().all()]


@router.get("/users", response_model=list[UserOut])
async def users_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserOut]:
    items = await services.UserService.list_all(session)
    return [UserOut.model_validate(x) for x in items]


@router.post("/users", response_model=UserOut, status_code=201)
async def user_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserOut:
    from sqlalchemy import select
    from app.core.models import User
    existing = await session.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username já existe")
    user = await services.UserService.create(session, payload.model_dump())
    return UserOut.model_validate(user)


@router.get("/users/{user_id}", response_model=UserOut)
async def user_detalhe(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserOut:
    try:
        user = await services.UserService.get(session, user_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Usuário não encontrado") from exc
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def user_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    payload: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserOut:
    try:
        user = await services.UserService.get(session, user_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Usuário não encontrado") from exc
    user = await services.UserService.update(session, user, payload.model_dump(exclude_unset=True))
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
async def user_deletar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        user = await services.UserService.get(session, user_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Usuário não encontrado") from exc
    user.is_active = False
    await session.flush()
    return None


@router.post("/users/{user_id}/reset-password", status_code=204)
async def user_reset_password(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    payload: PasswordResetPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        user = await services.UserService.get(session, user_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Usuário não encontrado") from exc
    await services.UserService.reset_password(session, user, payload.password)
    return None


# ---------------------------------------------------------------------------
# Sistema de Permissões v2
# ---------------------------------------------------------------------------


@router.get("/permissions", response_model=list[PermissionOut])
async def permissions_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PermissionOut]:
    from sqlalchemy import select
    from app.core.models import Permission
    result = await session.execute(select(Permission).order_by(Permission.categoria, Permission.nome))
    return [PermissionOut.model_validate(x) for x in result.scalars().all()]


@router.get("/roles", response_model=list[RoleOut])
async def roles_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[RoleOut]:
    from sqlalchemy import select
    from app.core.models import Role
    result = await session.execute(select(Role).order_by(Role.nome))
    return [RoleOut.model_validate(x) for x in result.scalars().all()]


@router.get("/users/{user_id}/permissions", response_model=UserPermissionsOut)
async def user_permissions_detalhe(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPermissionsOut:
    from app.core.models import Permission, Role, UserPermission, UserRole, RolePermission
    from sqlalchemy import select

    try:
        user = await services.UserService.get(session, user_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Usuário não encontrado") from exc

    scopes = await services.UserService.get_scopes(session, user.id)

    roles_result = await session.execute(
        select(RolePermission.role_id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    role_ids = {r for r in roles_result.scalars().all()}

    roles = await session.execute(select(Role).where(Role.id.in_(role_ids)))
    roles_out = [RoleSimpleOut.model_validate(r) for r in roles.scalars().all()]

    perms_result = await session.execute(
        select(Permission)
        .join(UserPermission, UserPermission.permission_id == Permission.id)
        .where(UserPermission.user_id == user_id, Permission.ativo.is_(True))
    )
    perms_out = [PermissionOut.model_validate(p) for p in perms_result.scalars().all()]

    return UserPermissionsOut(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        scopes=scopes,
        roles=roles_out,
        permissions=perms_out,
    )


@router.post("/users/{user_id}/permissions", status_code=204)
async def user_permission_adicionar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    from app.core.models import UserPermission
    perm_id = payload.get("permission_id")
    if not perm_id:
        raise HTTPException(400, "permission_id obrigatório")
    existing = await session.execute(
        select(UserPermission).where(UserPermission.user_id == user_id, UserPermission.permission_id == perm_id)
    )
    if existing.scalar_one_or_none():
        return None
    up = UserPermission(user_id=user_id, permission_id=perm_id)
    session.add(up)
    await session.flush()
    return None


@router.delete("/users/{user_id}/permissions/{permission_id}", status_code=204)
async def user_permission_remover(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    permission_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    from app.core.models import UserPermission
    result = await session.execute(
        select(UserPermission).where(UserPermission.user_id == user_id, UserPermission.permission_id == permission_id)
    )
    up = result.scalar_one_or_none()
    if up:
        await session.delete(up)
        await session.flush()
    return None


@router.post("/users/{user_id}/roles", status_code=204)
async def user_role_adicionar(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    from app.core.models import UserRole
    role_id = payload.get("role_id")
    if not role_id:
        raise HTTPException(400, "role_id obrigatório")
    existing = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    if existing.scalar_one_or_none():
        return None
    ur = UserRole(user_id=user_id, role_id=role_id)
    session.add(ur)
    await session.flush()
    return None


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def user_role_remover(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    user_id: int,
    role_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    from app.core.models import UserRole
    result = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    ur = result.scalar_one_or_none()
    if ur:
        await session.delete(ur)
        await session.flush()
    return None


@router.patch("/roles/{role_id}/permissions", status_code=204)
async def role_permissions_sync(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    role_id: int,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    from app.core.models import RolePermission, Role
    role = await session.get(Role, role_id)
    if role is None:
        raise HTTPException(404, "Papel não encontrado")
    permission_ids = payload.get("permission_ids", [])
    for rp in (await session.execute(select(RolePermission).where(RolePermission.role_id == role_id))).scalars().all():
        await session.delete(rp)
    for pid in permission_ids:
        session.add(RolePermission(role_id=role_id, permission_id=pid))
    await session.flush()
    return None


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=PaginatedAuditLogs)
async def audit_logs_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user_id: int | None = Query(default=None),
    method: str | None = Query(default=None),
    status_code: int | None = Query(default=None),
    data_inicio: str | None = Query(default=None),
    data_fim: str | None = Query(default=None),
) -> PaginatedAuditLogs:
    items, total = await services.AuditLogService.list_paginated(
        session,
        page=page,
        page_size=page_size,
        user_id=user_id,
        method=method,
        status_code=status_code,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    logs_out = []
    for item in items:
        out = AuditLogOut.model_validate(item)
        out.user_name = item.user.username if item.user else None
        logs_out.append(out)
    return PaginatedAuditLogs(
        items=logs_out,
        total=total,
        page=page,
        page_size=page_size,
    )
