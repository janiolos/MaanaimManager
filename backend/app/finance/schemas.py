"""Schemas Pydantic do módulo finance."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.finance.models import LancamentoFinanceiro


class _BaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------- CategoriaFinanceira ---------------------------


class CategoriaFinanceiraOut(_BaseModel):
    id: int
    nome: str
    tipo: str


class CategoriaFinanceiraCreate(BaseModel):
    nome: str
    tipo: str = Field(description="RECEITA | DESPESA")

    @field_validator("tipo")
    @classmethod
    def _valida_tipo(cls, v: str) -> str:
        if v not in LancamentoFinanceiro.TIPOS:
            raise ValueError(f"tipo deve ser um de {LancamentoFinanceiro.TIPOS}")
        return v


class CategoriaFinanceiraUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = Field(default=None, description="RECEITA | DESPESA")

    @field_validator("tipo")
    @classmethod
    def _valida_tipo(cls, v: str | None) -> str | None:
        if v is not None and v not in LancamentoFinanceiro.TIPOS:
            raise ValueError(f"tipo deve ser um de {LancamentoFinanceiro.TIPOS}")
        return v


# --------------------------- ContaCaixa ---------------------------


class ContaCaixaOut(_BaseModel):
    id: int
    nome: str
    ativo: bool


class ContaCaixaCreate(BaseModel):
    nome: str
    ativo: bool = True


class ContaCaixaUpdate(BaseModel):
    nome: str | None = None
    ativo: bool | None = None


# --------------------------- AnexoLancamento ---------------------------


class AnexoLancamentoOut(_BaseModel):
    id: int
    lancamento_id: int
    arquivo: str
    descricao: str
    enviado_por_id: int
    enviado_em: datetime


# --------------------------- LancamentoFinanceiro ---------------------------


class LancamentoOut(_BaseModel):
    id: int
    evento_id: int
    tipo: str
    categoria_id: int
    conta_id: int
    data: date
    descricao: str
    valor: Decimal
    forma_pagamento: str
    criado_por_id: int
    criado_em: datetime
    atualizado_por_id: int | None
    atualizado_em: datetime
    setor_origem: str | None
    pessoa: str | None
    assinatura_b64: str | None
    anexos: list[AnexoLancamentoOut] = []


class LancamentoCreate(BaseModel):
    tipo: str
    categoria_id: int
    conta_id: int
    data: date
    descricao: str
    valor: Decimal
    forma_pagamento: str
    setor_origem: str | None = None
    pessoa: str | None = None
    assinatura_b64: str | None = None

    @field_validator("tipo")
    @classmethod
    def _v_tipo(cls, v: str) -> str:
        if v not in LancamentoFinanceiro.TIPOS:
            raise ValueError(f"tipo deve ser um de {LancamentoFinanceiro.TIPOS}")
        return v

    @field_validator("forma_pagamento")
    @classmethod
    def _v_forma(cls, v: str) -> str:
        if v not in LancamentoFinanceiro.FORMAS_PAGAMENTO:
            raise ValueError(f"forma_pagamento deve ser um de {LancamentoFinanceiro.FORMAS_PAGAMENTO}")
        return v


class LancamentoUpdate(BaseModel):
    tipo: str | None = None
    categoria_id: int | None = None
    conta_id: int | None = None
    data: date | None = None
    descricao: str | None = None
    valor: Decimal | None = None
    forma_pagamento: str | None = None
    setor_origem: str | None = None
    pessoa: str | None = None
    assinatura_b64: str | None = None


# --------------------------- Dashboard ---------------------------


class DashboardKPIs(BaseModel):
    receitas: Decimal
    despesas: Decimal
    saldo: Decimal
    total_lancamentos: int
    por_forma_pagamento: dict[str, Decimal]
    por_categoria: dict[str, Decimal]


class PaginatedLancamentos(BaseModel):
    items: list[LancamentoOut]
    total: int
    page: int
    page_size: int


# --------------------------- Relatórios ---------------------------


class DRELine(BaseModel):
    categoria: str
    total: Decimal


class DREOut(BaseModel):
    data_inicio: date | None = None
    data_fim: date | None = None
    total_receitas: Decimal
    total_despesas: Decimal
    resultado_liquido: Decimal
    margem_percentual: float | None = None
    receitas_por_categoria: list[DRELine] = []
    despesas_por_categoria: list[DRELine] = []


class CashFlowLine(BaseModel):
    data: date
    receitas: Decimal
    despesas: Decimal
    saldo_dia: Decimal
    saldo_acumulado: Decimal


class CashFlowOut(BaseModel):
    linhas: list[CashFlowLine] = []
    total_receitas: Decimal
    total_despesas: Decimal
    saldo_final: Decimal


class ConciliacaoLine(BaseModel):
    forma_pagamento: str
    receitas: Decimal
    despesas: Decimal
    total: Decimal


class ConciliacaoOut(BaseModel):
    linhas: list[ConciliacaoLine] = []
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal


class OfficialReportLine(BaseModel):
    id: int
    data: date
    descricao: str
    categoria: str
    valor: Decimal
    forma_pagamento: str


class OfficialReportOut(BaseModel):
    receitas: list[OfficialReportLine] = []
    despesas: list[OfficialReportLine] = []
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal
    data_inicio: date | None = None
    data_fim: date | None = None