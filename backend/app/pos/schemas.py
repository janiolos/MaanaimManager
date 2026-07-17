"""Schemas Pydantic do módulo POS (PDV)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

class _BaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------- LocalVenda ---------------------------


class LocalVendaOut(_BaseModel):
    id: int
    evento_id: int | None
    nome: str
    ativo: bool
    modulo_dashboard: bool
    modulo_pdv: bool
    modulo_vendas: bool
    modulo_produtos: bool
    modulo_estoque: bool
    permite_desconto: bool
    desconto_maximo_perc: int
    permite_pagamento_misto: bool
    is_deposito_interno: bool
    caixa_aberto: bool
    caixa_aberto_em: datetime | None
    caixa_aberto_por_id: int | None
    caixa_atual_turno_id: int | None
    criado_em: datetime


class LocalVendaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    ativo: bool = True
    modulo_dashboard: bool = True
    modulo_pdv: bool = True
    modulo_vendas: bool = True
    modulo_produtos: bool = False
    modulo_estoque: bool = True
    permite_desconto: bool = True
    desconto_maximo_perc: int = Field(default=100, ge=0, le=100)
    permite_pagamento_misto: bool = True
    is_deposito_interno: bool = False


class LocalVendaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    ativo: bool | None = None
    modulo_dashboard: bool | None = None
    modulo_pdv: bool | None = None
    modulo_vendas: bool | None = None
    modulo_produtos: bool | None = None
    modulo_estoque: bool | None = None
    permite_desconto: bool | None = None
    desconto_maximo_perc: int | None = Field(default=None, ge=0, le=100)
    permite_pagamento_misto: bool | None = None
    is_deposito_interno: bool | None = None


# --------------------------- FamiliaVenda ---------------------------


class FamiliaVendaOut(_BaseModel):
    id: int
    local_id: int
    nome: str


class FamiliaVendaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)


# --------------------------- ProdutoLocal ---------------------------


class ProdutoLocalOut(_BaseModel):
    id: int
    produto_id: int
    local_id: int
    familia_id: int | None
    preco_venda: Decimal
    estoque_atual: Decimal
    estoque_minimo: Decimal
    ponto_reabastecimento: Decimal
    estoque_maximo: Decimal
    ativo: bool
    criado_em: datetime
    # nomes resolvidos
    produto_nome: str = ""
    produto_sku: str = ""
    familia_nome: str = ""


class ProdutoLocalCreate(BaseModel):
    produto_id: int
    familia_id: int | None = None
    preco_venda: Decimal = Field(default=Decimal("0.00"), ge=0)
    estoque_atual: Decimal = Field(default=Decimal("0.00"), ge=0)
    estoque_minimo: Decimal = Field(default=Decimal("0.00"), ge=0)
    ponto_reabastecimento: Decimal = Field(default=Decimal("0.00"), ge=0)
    estoque_maximo: Decimal = Field(default=Decimal("0.00"), ge=0)
    ativo: bool = True


class ProdutoLocalUpdate(BaseModel):
    familia_id: int | None = None
    preco_venda: Decimal | None = None
    estoque_minimo: Decimal | None = None
    ponto_reabastecimento: Decimal | None = None
    estoque_maximo: Decimal | None = None
    ativo: bool | None = None


# --------------------------- EntradaEstoqueLocal ---------------------------


class EntradaEstoqueLocalOut(_BaseModel):
    id: int
    produto_local_id: int
    quantidade: Decimal
    preco_custo: Decimal
    preco_venda: Decimal
    data: date
    observacao: str
    criado_por_id: int
    criado_em: datetime


class EntradaEstoqueLocalCreate(BaseModel):
    produto_local_id: int
    quantidade: Decimal = Field(gt=0)
    preco_custo: Decimal = Decimal("0.00")
    preco_venda: Decimal = Decimal("0.00")
    data: date
    observacao: str = ""


class TransferenciaEstoqueLocalCreate(BaseModel):
    produto_local_id: int
    quantidade: Decimal = Field(gt=0)
    data: date
    observacao: str = Field(default="", max_length=255)


class TransferenciaEstoqueLocalOut(_BaseModel):
    id: int
    produto_local_id: int
    quantidade: Decimal
    custo_unitario: Decimal
    data: date
    observacao: str
    criado_por_id: int
    criado_em: datetime


# --------------------------- VendaMobile ---------------------------


class ItemVendaIn(BaseModel):
    produto_local_id: int | None = None
    nome_produto: str = ""
    codigo_produto: str = ""
    familia_produto: str = ""
    quantidade: int = Field(ge=1)
    # Mantido no contrato para compatibilidade com clientes antigos. O backend
    # ignora este valor e usa sempre o preço cadastrado no ProdutoLocal.
    preco_unitario: Decimal = Field(default=Decimal("0.00"), ge=0)
    desconto_perc: Decimal = Decimal("0.00")

    @field_validator("desconto_perc")
    @classmethod
    def _clamp_desconto(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError("desconto deve ser entre 0 e 100")
        return v


class PagamentoIn(BaseModel):
    tipo: str = Field(description="DINHEIRO | PIX | DÉBITO | CRÉDITO")
    valor: Decimal = Field(gt=0)

    @field_validator("tipo")
    @classmethod
    def _normalize_tipo(cls, v: str) -> str:
        valid = {"DINHEIRO", "PIX", "DÉBITO", "CRÉDITO"}
        upper = v.upper().strip()
        if upper not in valid:
            raise ValueError(f"tipo deve ser um de {sorted(valid)}")
        return upper


class VendaCreate(BaseModel):
    local_id: int | None = None
    id_referencia: str = Field(min_length=1, max_length=50)
    itens: list[ItemVendaIn] = Field(min_length=1)
    pagamentos: list[PagamentoIn] = Field(min_length=1)


class ItemVendaOut(_BaseModel):
    id: int
    produto_local_id: int | None
    nome_produto: str
    codigo_produto: str
    familia_produto: str
    quantidade: int
    preco_unitario: Decimal
    desconto_perc: Decimal
    total_item: Decimal


class PagamentoOut(_BaseModel):
    id: int
    tipo: str
    valor: Decimal


class VendaOut(_BaseModel):
    id: int
    id_referencia: str
    evento_id: int
    local_id: int | None
    vendedor_id: int
    data_hora: datetime
    total: Decimal
    forma_pagamento: str
    turno_id: int | None
    itens: list[ItemVendaOut] = []
    pagamentos: list[PagamentoOut] = []


class PaginatedVendas(BaseModel):
    items: list[VendaOut]
    total: int
    page: int
    page_size: int


# --------------------------- PDV Dashboard ---------------------------


class TopProdutoDash(BaseModel):
    nome: str
    qtd: int
    receita: Decimal


class BaixoEstoqueDash(BaseModel):
    codigo: str
    nome: str
    familia: str
    status: str
    estoque: Decimal


class MargemProdutoDash(BaseModel):
    nome: str
    margem: Decimal


class PDVDashboard(BaseModel):
    # Backward compatibility keys
    total_vendas_hoje: Decimal
    quantidade_vendas_hoje: int
    ticket_medio: Decimal
    top_produtos: list[TopProdutoDash]
    vendas_por_pagamento: dict[str, Decimal]

    # Geral Tab
    receita_total: Decimal
    itens_vendidos: int
    itens_estoque: Decimal
    valor_estoque_venda: Decimal
    faturamento_por_evento: dict[str, Decimal]
    vendas_por_mes: dict[str, Decimal]
    top_10_mais_vendidos: list[TopProdutoDash]
    top_10_menos_vendidos: list[TopProdutoDash]

    # Vendas Tab
    lucro_liquido: Decimal
    receita_operacional: Decimal
    total_vendas: int
    receita_por_familia: dict[str, Decimal]
    ranking_mais_vendidos: list[TopProdutoDash]
    top_10_margem_lucro: list[MargemProdutoDash]

    # Estoque Tab
    custo_total_estoque: Decimal
    itens_fisicos_totais: Decimal
    valor_potencial_venda: Decimal
    estoque_por_familia_qtd: dict[str, Decimal]
    custo_por_familia_valor: dict[str, Decimal]
    produtos_baixo_estoque: list[BaixoEstoqueDash]

