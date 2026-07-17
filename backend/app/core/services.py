"""Serviços do módulo core."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import CentroCusto, ConfiguracaoEvento, ConfiguracaoSistema, Evento, User
from app.core.schemas import EventoCreate, EventoUpdate


class EventoService:
    """Operações sobre Evento (ciclo) - ancora central do sistema."""

    @staticmethod
    async def list_ativos(session: AsyncSession) -> Sequence[Evento]:
        stmt = select(Evento).where(Evento.ativo.is_(True)).order_by(Evento.data_inicio.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, evento_id: int) -> Evento:
        stmt = select(Evento).where(Evento.id == evento_id)
        result = await session.execute(stmt)
        evento = result.scalar_one_or_none()
        if evento is None:
            raise NoResultFound(f"Evento {evento_id} não encontrado")
        return evento

    @staticmethod
    async def create(session: AsyncSession, payload: EventoCreate) -> Evento:
        evento = Evento(**payload.model_dump())
        session.add(evento)
        await session.flush()
        # Cria configuração padrão do evento
        config = ConfiguracaoEvento(evento_id=evento.id)
        session.add(config)
        await session.flush()
        return evento

    @staticmethod
    async def encerrar(session: AsyncSession, evento: Evento, user_id: int) -> Evento:
        from app.pos.models import LocalVenda, ProdutoLocal
        from app.inventory.models import Produto

        evento.status = Evento.ENCERRADO
        evento.fechado = True

        config = await session.execute(
            select(ConfiguracaoEvento).where(ConfiguracaoEvento.evento_id == evento.id)
        )
        config = config.scalar_one_or_none()
        if config is None:
            config = ConfiguracaoEvento(evento_id=evento.id)
            session.add(config)
        from datetime import datetime, timezone
        config.data_fechamento = datetime.now(timezone.utc)

        # Zera estoque de produtos não-perenes nos locais do evento
        locais_result = await session.execute(
            select(LocalVenda.id).where(LocalVenda.evento_id == evento.id)
        )
        locais_ids = [r[0] for r in locais_result.all()]
        if locais_ids:
            pl_result = await session.execute(
                select(ProdutoLocal)
                .where(ProdutoLocal.local_id.in_(locais_ids))
                .options(selectinload(ProdutoLocal.produto))
            )
            for pl in pl_result.scalars().all():
                if pl.produto and not pl.produto.perene:
                    pl.estoque_atual = Decimal("0.00")

        await session.flush()
        return evento

    @staticmethod
    async def update(session: AsyncSession, evento: Evento, payload: EventoUpdate) -> Evento:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(evento, key, value)
        await session.flush()
        return evento


class ConfiguracaoService:
    """Singleton de ConfiguracaoSistema (pk=1)."""

    @staticmethod
    async def get_solo(session: AsyncSession) -> ConfiguracaoSistema:
        stmt = select(ConfiguracaoSistema).where(ConfiguracaoSistema.id == 1)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            config = ConfiguracaoSistema(id=1)
            session.add(config)
            await session.flush()
        return config

    @staticmethod
    async def update(
        session: AsyncSession,
        config: ConfiguracaoSistema,
        payload: dict,
    ) -> ConfiguracaoSistema:
        for k, v in payload.items():
            if v is not None:
                setattr(config, k, v)
        await session.flush()
        return config


class ConfiguracaoEventoService:
    @staticmethod
    async def get_or_create(session: AsyncSession, evento_id: int) -> ConfiguracaoEvento:
        stmt = select(ConfiguracaoEvento).where(ConfiguracaoEvento.evento_id == evento_id)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            config = ConfiguracaoEvento(evento_id=evento_id)
            session.add(config)
            await session.flush()
        return config

    @staticmethod
    async def update(
        session: AsyncSession,
        config: ConfiguracaoEvento,
        payload: dict,
    ) -> ConfiguracaoEvento:
        for k, v in payload.items():
            if v is not None:
                setattr(config, k, v)
        await session.flush()
        return config


class CentroCustoService:
    @staticmethod
    async def list_ativos(session: AsyncSession) -> Sequence[CentroCusto]:
        from app.core.models import CentroCusto
        stmt = select(CentroCusto).where(CentroCusto.ativo.is_(True)).order_by(CentroCusto.nome)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def list_all(session: AsyncSession) -> Sequence[CentroCusto]:
        from app.core.models import CentroCusto
        stmt = select(CentroCusto).order_by(CentroCusto.nome)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, cc_id: int) -> CentroCusto:
        from app.core.models import CentroCusto
        cc = await session.get(CentroCusto, cc_id)
        if cc is None:
            raise NoResultFound(f"Centro de custo {cc_id} não encontrado")
        return cc

    @staticmethod
    async def create(session: AsyncSession, payload: dict) -> CentroCusto:
        from app.core.models import CentroCusto
        cc = CentroCusto(**payload)
        session.add(cc)
        await session.flush()
        return cc

    @staticmethod
    async def update(session: AsyncSession, cc: CentroCusto, payload: dict) -> CentroCusto:
        for k, v in payload.items():
            if v is not None:
                setattr(cc, k, v)
        await session.flush()
        return cc

    @staticmethod
    async def delete(session: AsyncSession, cc: CentroCusto) -> None:
        await session.delete(cc)
        await session.flush()


class UserService:
    @staticmethod
    async def list_all(session: AsyncSession) -> Sequence[User]:
        from app.core.models import User
        stmt = select(User).order_by(User.first_name, User.last_name)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def list_ativos(session: AsyncSession) -> Sequence[User]:
        from app.core.models import User
        stmt = select(User).where(User.is_active.is_(True)).order_by(User.first_name, User.last_name)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> User:
        from app.core.models import User
        user = await session.get(User, user_id)
        if user is None:
            raise NoResultFound(f"User {user_id} não encontrado")
        return user

    @staticmethod
    async def get_scopes(session: AsyncSession, user_id: int) -> list[str]:
        """Retorna scopes do usuário a partir das novas tabelas de permissão + roles."""
        from app.core.models import Permission, UserPermission, UserRole, RolePermission

        # Scopes diretos do usuário
        direct = await session.execute(
            select(Permission.scope)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.user_id == user_id, Permission.ativo.is_(True))
        )
        scopes = set(direct.scalars().all())

        # Scopes via roles
        role_perms = await session.execute(
            select(Permission.scope)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id, Permission.ativo.is_(True))
        )
        scopes.update(role_perms.scalars().all())

        # Sempre incluir core:read se o usuário tiver alguma permissão
        if scopes:
            scopes.add("core:read")
        return sorted(scopes)

    @staticmethod
    async def create(session: AsyncSession, payload: dict) -> User:
        from app.core.models import User, Group
        from app.auth.passwords import hash_password
        user = User(
            username=payload["username"],
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            email=payload.get("email", ""),
            password=hash_password(payload["password"]),
            is_active=payload.get("is_active", True),
            is_superuser=payload.get("is_superuser", False),
            is_staff=payload.get("is_staff", False),
        )
        if payload.get("group_ids"):
            groups = await session.execute(select(Group).where(Group.id.in_(payload["group_ids"])))
            user.groups = groups.scalars().all()
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def update(session: AsyncSession, user: User, payload: dict) -> User:
        from app.core.models import Group
        for k, v in payload.items():
            if k == "group_ids" and v is not None:
                groups = await session.execute(select(Group).where(Group.id.in_(v)))
                user.groups = groups.scalars().all()
            elif v is not None:
                setattr(user, k, v)
        await session.flush()
        return user

    @staticmethod
    async def reset_password(session: AsyncSession, user: User, new_password: str) -> None:
        from app.auth.passwords import hash_password
        user.password = hash_password(new_password)
        await session.flush()


class AuditLogService:
    @staticmethod
    async def list_paginated(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        user_id: int | None = None,
        method: str | None = None,
        status_code: int | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> tuple[Sequence, int]:
        from app.core.models import AuditLog
        base = select(AuditLog)
        if user_id is not None:
            base = base.where(AuditLog.user_id == user_id)
        if method is not None:
            base = base.where(AuditLog.method == method.upper())
        if status_code is not None:
            base = base.where(AuditLog.status_code == status_code)
        if data_inicio is not None:
            base = base.where(AuditLog.created_at >= data_inicio)
        if data_fim is not None:
            base = base.where(AuditLog.created_at <= data_fim)

        # count first
        count_q = select(func.count()).select_from(base.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        base = base.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = (await session.execute(base)).scalars().all()
        return items, total
