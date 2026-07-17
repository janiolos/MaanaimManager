"""Schemas Pydantic do módulo core."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.models import Evento


class CentroCustoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codigo: str
    ativo: bool


class CentroCustoCreate(BaseModel):
    nome: str
    codigo: str
    ativo: bool = True


class CentroCustoUpdate(BaseModel):
    nome: str | None = None
    codigo: str | None = None
    ativo: bool | None = None


class EventoBase(BaseModel):
    nome: str
    data_inicio: datetime
    data_fim: datetime
    ativo: bool = True
    status: str = Evento.PLANEJADO
    fechado: bool = False
    taxa_base: Decimal = Decimal("50.00")
    taxa_trabalhador: Decimal = Decimal("25.00")
    adicional_chale: Decimal = Decimal("100.00")
    prev_participantes: int | None = None
    prev_trabalhadores: int | None = None
    observacoes: str = ""
    centro_custo_id: int | None = None
    responsavel_geral_id: int | None = None


class EventoCreate(EventoBase):
    pass


class EventoUpdate(BaseModel):
    nome: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    ativo: bool | None = None
    status: str | None = None
    fechado: bool | None = None
    taxa_base: Decimal | None = None
    taxa_trabalhador: Decimal | None = None
    adicional_chale: Decimal | None = None
    prev_participantes: int | None = None
    prev_trabalhadores: int | None = None
    observacoes: str | None = None
    centro_custo_id: int | None = None
    responsavel_geral_id: int | None = None


class EventoOut(EventoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ConfiguracaoSistemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_sistema: str
    rotulo_evento_singular: str
    rotulo_evento_plural: str
    modulo_financeiro_ativo: bool
    modulo_estoque_ativo: bool
    modulo_hospedagem_ativo: bool
    modulo_notificacoes_ativo: bool
    modulo_pos_ativo: bool


class ConfiguracaoSistemaUpdate(BaseModel):
    nome_sistema: str | None = None
    rotulo_evento_singular: str | None = None
    rotulo_evento_plural: str | None = None
    modulo_financeiro_ativo: bool | None = None
    modulo_estoque_ativo: bool | None = None
    modulo_hospedagem_ativo: bool | None = None
    modulo_notificacoes_ativo: bool | None = None
    modulo_pos_ativo: bool | None = None


class ConfiguracaoEventoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evento_id: int
    permite_vendas_pos: bool
    permite_edicao_estoque_pos: bool
    permite_lancamentos_financeiro: bool
    data_fechamento: datetime | None
    criado_em: datetime
    atualizado_em: datetime


class ConfiguracaoEventoUpdate(BaseModel):
    permite_vendas_pos: bool | None = None
    permite_edicao_estoque_pos: bool | None = None
    permite_lancamentos_financeiro: bool | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_name: str | None = None
    method: str
    path: str
    view_name: str
    status_code: int
    ip_address: str | None
    user_agent: str
    created_at: datetime


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


class UserSimpleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    is_active: bool
    is_superuser: bool
    is_staff: bool
    groups: list[GroupOut]


class UserCreate(BaseModel):
    username: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    password: str
    is_active: bool = True
    is_superuser: bool = False
    is_staff: bool = False
    group_ids: list[int] = []


class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_staff: bool | None = None
    group_ids: list[int] | None = None


class PasswordResetPayload(BaseModel):
    password: str


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scope: str
    nome: str
    descricao: str
    categoria: str
    ativo: bool


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str
    ativo: bool
    permissions: list[PermissionOut] = []


class RoleSimpleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str
    ativo: bool


class UserPermissionsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    is_active: bool
    is_superuser: bool
    scopes: list[str] = []
    roles: list[RoleSimpleOut] = []
    permissions: list[PermissionOut] = []