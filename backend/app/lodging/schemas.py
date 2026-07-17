"""Schemas Pydantic do módulo lodging."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _BM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============================ Chale ============================


class ChaleOut(_BM):
    id: int
    codigo: str
    capacidade: int
    status: str
    acessivel_cadeirante: bool
    observacoes: str


class ChaleCreate(BaseModel):
    codigo: str
    capacidade: int = Field(gt=0)
    status: str = "ATIVO"
    acessivel_cadeirante: bool = False
    observacoes: str = ""

    @field_validator("status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        from app.lodging.models import Chale
        if v not in Chale.STATUS_CHOICES:
            raise ValueError(f"status deve ser um de {Chale.STATUS_CHOICES}")
        return v


class ChaleUpdate(BaseModel):
    codigo: str | None = None
    capacidade: int | None = Field(default=None, gt=0)
    status: str | None = None
    acessivel_cadeirante: bool | None = None
    observacoes: str | None = None


# ============================ ReservaChale ============================


class ReservaOut(_BM):
    id: int
    evento_id: int
    chale_id: int
    data_entrada: date | None
    data_saida: date | None
    responsavel_nome: str
    qtd_pessoas: int
    qtd_criancas: int
    idades_criancas: str
    possui_necessidade_especial: bool
    detalhes_necessidade_especial: str
    status: str
    valor_adicional: Decimal
    pago: bool
    forma_pagamento: str
    conta_id: int | None
    lancamento_financeiro_id: int | None
    observacoes: str
    criado_por_id: int
    criado_em: datetime
    atualizado_por_id: int | None
    atualizado_em: datetime


class ReservaCreate(BaseModel):
    chale_id: int
    data_entrada: date
    data_saida: date
    responsavel_nome: str
    qtd_pessoas: int = Field(gt=0)
    qtd_criancas: int = Field(default=0, ge=0)
    idades_criancas: str = ""
    possui_necessidade_especial: bool = False
    detalhes_necessidade_especial: str = ""
    valor_adicional: Decimal = Decimal("0.00")
    pago: bool = False
    forma_pagamento: str = ""
    conta_id: int | None = None
    observacoes: str = ""


class ReservaUpdate(BaseModel):
    chale_id: int | None = None
    data_entrada: date | None = None
    data_saida: date | None = None
    responsavel_nome: str | None = None
    qtd_pessoas: int | None = Field(default=None, gt=0)
    qtd_criancas: int | None = Field(default=None, ge=0)
    idades_criancas: str | None = None
    possui_necessidade_especial: bool | None = None
    detalhes_necessidade_especial: str | None = None
    status: str | None = None
    valor_adicional: Decimal | None = None
    pago: bool | None = None
    forma_pagamento: str | None = None
    conta_id: int | None = None
    observacoes: str | None = None


# ============================ AcaoChale ============================


class AcaoOut(_BM):
    id: int
    evento_id: int
    chale_id: int
    tipo: str
    titulo: str
    data_inicio: date
    data_fim: date
    descricao: str
    ativo: bool
    criado_por_id: int
    criado_em: datetime


class AcaoCreate(BaseModel):
    chale_id: int
    tipo: str
    titulo: str
    data_inicio: date
    data_fim: date
    descricao: str = ""
    ativo: bool = True

    @field_validator("tipo")
    @classmethod
    def _v_tipo(cls, v: str) -> str:
        from app.lodging.models import AcaoChale
        if v not in AcaoChale.TIPO_CHOICES:
            raise ValueError(f"tipo deve ser um de {AcaoChale.TIPO_CHOICES}")
        return v


class AcaoUpdate(BaseModel):
    chale_id: int | None = None
    tipo: str | None = None
    titulo: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    descricao: str | None = None
    ativo: bool | None = None


# ============================ Dashboard ============================


class LodgingDashboard(BaseModel):
    total_chales: int
    chales_ativos: int
    chales_manutencao: int
    reservas_ativas: int
    reservas_confirmadas: int
    acoes_ativas: int


# ============================ Mapa ============================


class MapaCell(BaseModel):
    chale_id: int
    chale_codigo: str
    data: date
    tipo: str  # "RESERVA" | "ACAO" | "LIVRE"
    label: str
    reserva_id: int | None = None
    acao_id: int | None = None


class MapaResponse(BaseModel):
    chales: list[ChaleOut]
    dias: list[date]
    celulas: list[list[MapaCell] | None]