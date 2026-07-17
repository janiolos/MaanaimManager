"""Schemas Pydantic do módulo inventory."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.inventory.models import CotacaoCompra, Produto, RequisicaoSaida


class _BM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============================ Produto ============================


class ProdutoOut(_BM):
    id: int
    nome: str
    sku: str
    categoria: str
    unidade: str
    estoque_atual: Decimal
    estoque_minimo: Decimal
    estoque_reabastecimento: Decimal
    estoque_maximo: Decimal
    valor_estoque_atual: Decimal
    custo_medio_atual: Decimal
    perene: bool
    ativo: bool


class ProdutoCreate(BaseModel):
    nome: str
    sku: str
    categoria: str = Produto.MATERIA_PRIMA
    unidade: str = "UN"
    estoque_minimo: Decimal = Decimal("0.00")
    estoque_reabastecimento: Decimal = Decimal("0.00")
    estoque_maximo: Decimal = Decimal("0.00")
    perene: bool = False
    ativo: bool = True

    @field_validator("categoria")
    @classmethod
    def _v_cat(cls, v: str) -> str:
        if v not in Produto.CATEGORIA_CHOICES:
            raise ValueError(f"categoria deve ser um de {Produto.CATEGORIA_CHOICES}")
        return v


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    sku: str | None = None
    categoria: str | None = None
    unidade: str | None = None
    estoque_minimo: Decimal | None = None
    estoque_reabastecimento: Decimal | None = None
    estoque_maximo: Decimal | None = None
    perene: bool | None = None
    ativo: bool | None = None


# ============================ EntradaEstoque ============================


class EntradaEstoqueOut(_BM):
    id: int
    produto_id: int
    data: date
    quantidade: Decimal
    custo_unitario: Decimal
    documento: str
    observacao: str
    criado_por_id: int
    criado_em: datetime


class EntradaEstoqueCreate(BaseModel):
    produto_id: int
    data: date
    quantidade: Decimal
    custo_unitario: Decimal = Decimal("0.00")
    documento: str = ""
    observacao: str = ""


# ============================ RequisicaoSaida ============================


class RequisicaoItemOut(_BM):
    id: int
    requisicao_id: int
    produto_id: int
    local_origem_id: int | None
    quantidade: Decimal
    custo_medio_unitario: Decimal
    custo_total: Decimal
    saldo_antes: Decimal
    saldo_depois: Decimal


class RequisicaoItemIn(BaseModel):
    produto_id: int
    local_origem_id: int | None = None
    quantidade: Decimal

    @field_validator("quantidade")
    @classmethod
    def _v_qtd(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantidade deve ser > 0")
        return v


class RequisicaoOut(_BM):
    id: int
    numero: str
    evento_id: int
    area: str
    data_solicitacao: datetime
    status: str
    observacao: str
    protocolo: uuid.UUID
    finalizado_em: datetime | None
    finalizado_por_id: int | None
    criado_por_id: int
    criado_em: datetime
    itens: list[RequisicaoItemOut] = []


class RequisicaoCreate(BaseModel):
    area: str
    observacao: str = ""
    itens: list[RequisicaoItemIn]

    @field_validator("area")
    @classmethod
    def _v_area(cls, v: str) -> str:
        if v not in RequisicaoSaida.AREAS_CHOICES:
            raise ValueError(f"area deve ser um de {RequisicaoSaida.AREAS_CHOICES}")
        return v

    @field_validator("itens")
    @classmethod
    def _v_itens(cls, v: list[RequisicaoItemIn]) -> list[RequisicaoItemIn]:
        if not v:
            raise ValueError("requisição precisa de pelo menos 1 item")
        # checa unicidade de produto
        ids = [i.produto_id for i in v]
        if len(set(ids)) != len(ids):
            raise ValueError("itens não podem repetir o mesmo produto")
        return v


class RequisicaoUpdate(BaseModel):
    area: str | None = None
    observacao: str | None = None
    itens: list[RequisicaoItemIn] | None = None


# ============================ Fornecedor ============================


class FornecedorOut(_BM):
    id: int
    nome: str
    documento: str
    contato: str
    telefone: str
    email: str
    ativo: bool
    criado_em: datetime


class FornecedorCreate(BaseModel):
    nome: str
    documento: str = ""
    contato: str = ""
    telefone: str = ""
    email: str = ""
    ativo: bool = True


class FornecedorUpdate(BaseModel):
    nome: str | None = None
    documento: str | None = None
    contato: str | None = None
    telefone: str | None = None
    email: str | None = None
    ativo: bool | None = None


# ============================ CotacaoCompra ============================


class CotacaoPrecoOut(_BM):
    id: int
    fornecedor_id: int
    valor_unitario: Decimal
    valor_total: Decimal


class CotacaoItemOut(_BM):
    id: int
    produto_id: int
    quantidade: Decimal
    precos: list[CotacaoPrecoOut] = []


class CotacaoOut(_BM):
    id: int
    numero: str
    evento_id: int
    status: str
    observacao: str
    criado_por_id: int
    criado_em: datetime
    fornecedor_aprovado_id: int | None
    valor_aprovado: Decimal | None
    aprovado_em: datetime | None
    aprovado_por_id: int | None
    fechado_em: datetime | None
    fechado_por_id: int | None
    lancamento_financeiro_id: int | None
    itens: list[CotacaoItemOut] = []


class CotacaoPrecoIn(BaseModel):
    fornecedor_id: int
    valor_unitario: Decimal


class CotacaoItemIn(BaseModel):
    produto_id: int
    quantidade: Decimal
    precos: list[CotacaoPrecoIn] = []

    @field_validator("quantidade")
    @classmethod
    def _v_qtd(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantidade deve ser > 0")
        return v


class CotacaoCreate(BaseModel):
    observacao: str = ""
    itens: list[CotacaoItemIn]

    @field_validator("itens")
    @classmethod
    def _v_itens(cls, v: list[CotacaoItemIn]) -> list[CotacaoItemIn]:
        if not v:
            raise ValueError("cotação precisa de pelo menos 1 item")
        ids = [i.produto_id for i in v]
        if len(set(ids)) != len(ids):
            raise ValueError("itens não podem repetir o mesmo produto")
        return v


class CotacaoUpdate(BaseModel):
    observacao: str | None = None
    itens: list[CotacaoItemIn] | None = None


class CotacaoAprovarIn(BaseModel):
    """Payload para aprovar cotação - cria LancamentoFinanceiro DESPESA + OrdemCompra + entrada estoque."""

    fornecedor_id: int
    categoria_despesa_id: int
    conta_id: int
    forma_pagamento: str = "OUTRO"
    data: date
    observacao: str = ""

    @field_validator("forma_pagamento")
    @classmethod
    def _v_forma(cls, v: str) -> str:
        # valida contra choices de finance
        from app.finance.models import LancamentoFinanceiro
        if v not in LancamentoFinanceiro.FORMAS_PAGAMENTO:
            raise ValueError(f"forma_pagamento deve ser um de {LancamentoFinanceiro.FORMAS_PAGAMENTO}")
        return v


class OrdemCompraOut(_BM):
    id: int
    numero: str
    cotacao_id: int
    fornecedor_id: int
    fornecedor_nome: str = ""
    mensagem: str
    valor_total: Decimal
    status_envio: str
    enviada_em: datetime | None
    criado_por_id: int
    criado_por_nome: str = ""
    evento_id: int | None = None
    criado_em: datetime


class PaginatedOrdensCompra(BaseModel):
    items: list[OrdemCompraOut]
    total: int
    page: int
    page_size: int


# ============================ Dashboard ============================


class InventoryDashboard(BaseModel):
    total_produtos: int
    produtos_ativos: int
    estoque_baixo: int
    estoque_reabastecer: int
    valor_total_estoque: Decimal
    requisicoes_abertas: int
    cotacoes_abertas: int


class PaginatedProdutos(BaseModel):
    items: list[ProdutoOut]
    total: int
    page: int
    page_size: int