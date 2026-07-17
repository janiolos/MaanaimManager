"""Modelos do módulo core.

Espelham as tabelas já criadas pelo Django (vide apps/core/migrations/*.py).
Nenhuma migration cria tabelas - o Alembic baseline assume o schema atual.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# --------------------------- Auth (tables auth_user, auth_group) ---------------------------


class User(Base):
    __tablename__ = "auth_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    first_name: Mapped[str] = mapped_column(String(150), default="")
    last_name: Mapped[str] = mapped_column(String(150), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    groups: Mapped[list[Group]] = relationship(
        secondary="auth_user_groups",
        back_populates="users",
        lazy="selectin",
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_role",
        lazy="selectin",
    )

    user_permissions: Mapped[list["UserPermission"]] = relationship(
        lazy="selectin",
    )


class Group(Base):
    __tablename__ = "auth_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)

    users: Mapped[list[User]] = relationship(
        secondary="auth_user_groups",
        back_populates="groups",
        lazy="selectin",
    )


# M2M explícita para preservar nome/tabela do Django auth_user_groups
from sqlalchemy import Column, Table  # noqa: E402

auth_user_groups = Table(
    "auth_user_groups",
    Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("auth_user.id"), nullable=False),
    Column("group_id", Integer, ForeignKey("auth_group.id"), nullable=False),
    extend_existing=True,
    info={"django_managed": True},
)


# --------------------------- core_centrocusto ---------------------------


class CentroCusto(Base):
    __tablename__ = "core_centrocusto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


# --------------------------- core_evento ---------------------------


class Evento(Base):
    __tablename__ = "core_evento"

    PLANEJADO = "PLANEJADO"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    ENCERRADO = "ENCERRADO"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255))
    data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default=PLANEJADO)
    fechado: Mapped[bool] = mapped_column(Boolean, default=False)
    taxa_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("50.00"))
    taxa_trabalhador: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("25.00"))
    adicional_chale: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("100.00"))
    prev_participantes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prev_trabalhadores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, default="")

    responsavel_geral_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    responsavel_geral: Mapped[User | None] = relationship(lazy="selectin")

    centro_custo_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core_centrocusto.id"), nullable=True
    )
    centro_custo: Mapped[CentroCusto | None] = relationship(lazy="selectin")


# --------------------------- core_auditlog ---------------------------


class AuditLog(Base):
    __tablename__ = "core_auditlog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    user: Mapped[User | None] = relationship(lazy="selectin")

    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(2048))
    view_name: Mapped[str] = mapped_column(String(255), default="")
    status_code: Mapped[int] = mapped_column(SmallInteger)
    ip_address: Mapped[str | None] = mapped_column(String(39), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --------------------------- core_configuracaosistema ---------------------------


class ConfiguracaoEvento(Base):
    __tablename__ = "core_configuracaoevento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core_evento.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    evento: Mapped[Evento] = relationship(lazy="selectin")

    permite_vendas_pos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permite_edicao_estoque_pos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permite_lancamentos_financeiro: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_fechamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ConfiguracaoSistema(Base):
    __tablename__ = "core_configuracaosistema"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome_sistema: Mapped[str] = mapped_column(String(80), default="CycloHub")
    rotulo_evento_singular: Mapped[str] = mapped_column(String(40), default="Evento")
    rotulo_evento_plural: Mapped[str] = mapped_column(String(40), default="Eventos")
    modulo_financeiro_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    modulo_estoque_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    modulo_hospedagem_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    modulo_notificacoes_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    modulo_pos_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --------------------------- Sistema de Permissões v2 ---------------------------


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="", nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), default="geral", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permission",
        lazy="selectin",
    )


class RolePermission(Base):
    __tablename__ = "role_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("permission.id", ondelete="CASCADE"), nullable=False)


class UserPermission(Base):
    __tablename__ = "user_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("permission.id", ondelete="CASCADE"), nullable=False)

    permission: Mapped["Permission"] = relationship(lazy="selectin")


class UserRole(Base):
    __tablename__ = "user_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id", ondelete="CASCADE"), nullable=False)

    role: Mapped["Role"] = relationship(lazy="selectin", overlaps="roles")