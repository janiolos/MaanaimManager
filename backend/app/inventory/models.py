"""Modelos do módulo inventory - espelham tabelas Django `inventory_*`.

Reescrita do `apps/inventory/models.py` para SQLAlchemy 2.0 com tipos async.
Campos Twilio em OrdemCompra (twilio_sid, erro_envio) foram REMOVIDOS por decisão
de design - a integração WhatsApp será refeita no futuro.

Tables (nomes preservados do Django legado):
- inventory_produto
- inventory_movimentoestoque (LEGADO - preservada só para histórico)
- inventory_entradaestoque
- inventory_requisicaosaida
- inventory_requisicaosaidaitem
- inventory_requisicaosaidaimpressao
- inventory_fornecedor
- inventory_cotacaocompra
- inventory_cotacaocompraitem
- inventory_cotacaocomprecpreco
- inventory_cotacaocompraimpressao
- inventory_ordemcompra
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.core.models import Evento, User
    from app.finance.models import LancamentoFinanceiro


# ============================ Produto ============================


class Produto(Base):
    """Catálogo de produtos com estoque próprio (média ponderada)."""

    __tablename__ = "inventory_produto"

    MATERIA_PRIMA = "MATERIA_PRIMA"
    PRODUTO_ACABADO = "PRODUTO_ACABADO"
    COMPONENTE = "COMPONENTE"
    CATEGORIA_CHOICES = (MATERIA_PRIMA, PRODUTO_ACABADO, COMPONENTE)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(140))
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    categoria: Mapped[str] = mapped_column(String(30), default=MATERIA_PRIMA)
    unidade: Mapped[str] = mapped_column(String(20), default="UN")

    estoque_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    estoque_reabastecimento: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    estoque_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    valor_estoque_atual: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"))
    custo_medio_atual: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0000"))

    perene: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    entradas: Mapped[list[EntradaEstoque]] = relationship(
        back_populates="produto", lazy="selectin"
    )


# ============================ EntradaEstoque ============================


class EntradaEstoque(Base):
    __tablename__ = "inventory_entradaestoque"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_produto.id"), nullable=False
    )
    produto: Mapped[Produto] = relationship(back_populates="entradas", lazy="selectin")

    data: Mapped[date] = mapped_column(Date)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    documento: Mapped[str] = mapped_column(String(120), default="")
    observacao: Mapped[str] = mapped_column(String(255), default="")

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"), nullable=False)
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================ MovimentoEstoque (LEGADO) ============================


class MovimentoEstoque(Base):
    """Modelo legado - preservado para histórico (sem escrita nova)."""

    __tablename__ = "inventory_movimentoestoque"

    SAIDA = "SAIDA"
    DEVOLUCAO = "DEVOLUCAO"
    TIPOS = (SAIDA, DEVOLUCAO)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(12))
    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"))
    produto_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inventory_produto.id"))
    data: Mapped[date] = mapped_column(Date)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    observacao: Mapped[str] = mapped_column(String(255), default="")

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================ RequisicaoSaida + Extras ============================


class RequisicaoSaida(Base):
    """Requisição de saída de estoque para um setor/área.

    Workflows: ABERTA -> FINALIZADA | CANCELADA. Finalização baixa estoque
    atomicamente e grava snapshot de saldo/custo por item.
    """

    __tablename__ = "inventory_requisicaosaida"

    ABERTA = "ABERTA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = (ABERTA, FINALIZADA, CANCELADA)

    COZINHA = "COZINHA"
    COPA = "COPA"
    CANTINA = "CANTINA"
    COPA_PASTORES = "COPA_PASTORES"
    SECRETARIA = "SECRETARIA"
    AREAS_CHOICES = (COZINHA, COPA, CANTINA, COPA_PASTORES, SECRETARIA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True, default="")
    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"))
    evento: Mapped[Evento] = relationship(lazy="selectin")

    area: Mapped[str] = mapped_column(String(80))
    data_solicitacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(12), default=ABERTA)
    observacao: Mapped[str] = mapped_column(String(255), default="")

    protocolo: Mapped[uuid.UUID] = mapped_column(unique=True, default=uuid.uuid4)

    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalizado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )

    impresso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    impresso_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    itens: Mapped[list[RequisicaoSaidaItem]] = relationship(
        back_populates="requisicao",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="RequisicaoSaidaItem.id",
    )


class RequisicaoSaidaItem(Base):
    __tablename__ = "inventory_requisicaosaidaitem"
    __table_args__ = (UniqueConstraint("requisicao_id", "produto_id", name="uniq_req_produto"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requisicao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_requisicaosaida.id"), nullable=False
    )
    requisicao: Mapped[RequisicaoSaida] = relationship(back_populates="itens")

    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_produto.id"), nullable=False
    )
    produto: Mapped[Produto] = relationship(lazy="selectin")

    local_origem_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_localvenda.id"), nullable=True
    )

    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    # Snapshot preenchido em `RequisicaoService.finalizar`
    custo_medio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000")
    )
    custo_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"))
    saldo_antes: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    saldo_depois: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))


class RequisicaoSaidaImpressao(Base):
    """Auditoria de impressões de comprovante (1a via, 2a via, etc)."""

    __tablename__ = "inventory_requisicaosaidaimpressao"

    ORIGINAL = "ORIGINAL"
    SEGUNDA_VIA = "2A_VIA"
    VIA_CHOICES = (ORIGINAL, SEGUNDA_VIA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requisicao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_requisicaosaida.id"), nullable=False
    )
    requisicao: Mapped[RequisicaoSaida] = relationship(lazy="selectin")

    impresso_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    impresso_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    impresso_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[impresso_por_id])
    via: Mapped[str] = mapped_column(String(20), default=ORIGINAL)


# ============================ Fornecedor ============================


class Fornecedor(Base):
    __tablename__ = "inventory_fornecedor"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(140), unique=True)
    documento: Mapped[str] = mapped_column(String(30), default="")
    contato: Mapped[str] = mapped_column(String(120), default="")
    telefone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(254), default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================ CotacaoCompra + Extras ============================


class CotacaoCompra(Base):
    """Cotação de compra com grade de preços por fornecedor. Finalização workflow:
    ABERTA -> FECHADA (sem OC) ou -> FECHADA com OrdemCompra (aprovação).

    Aprovação: cria LancamentoFinanceiro DESPESA + OrdemCompra + registra entrada em estoque.
    """

    __tablename__ = "inventory_cotacaocompra"

    ABERTA = "ABERTA"
    FECHADA = "FECHADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = (ABERTA, FECHADA, CANCELADA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True, default="")
    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"))
    evento: Mapped[Evento] = relationship(lazy="selectin")

    data_cotacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(12), default=ABERTA)
    observacao: Mapped[str] = mapped_column(String(255), default="")

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])

    fornecedor_aprovado_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("inventory_fornecedor.id"), nullable=True
    )
    fornecedor_aprovado: Mapped[Fornecedor | None] = relationship(lazy="selectin")

    valor_aprovado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aprovado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )

    # FK cross-app -> finance; nullable para requisições não pagas
    lancamento_financeiro_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("finance_lancamentofinanceiro.id"), nullable=True
    )
    lancamento_financeiro: Mapped[LancamentoFinanceiro | None] = relationship(lazy="selectin")

    fechado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fechado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )

    itens: Mapped[list[CotacaoCompraItem]] = relationship(
        back_populates="cotacao",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CotacaoCompraItem.id",
    )
    ordem_compra: Mapped[OrdemCompra | None] = relationship(
        back_populates="cotacao", lazy="selectin", uselist=False
    )

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CotacaoCompraItem(Base):
    __tablename__ = "inventory_cotacaocompraitem"
    __table_args__ = (
        UniqueConstraint("cotacao_id", "produto_id", name="uniq_cotacao_produto"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cotacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_cotacaocompra.id"), nullable=False
    )
    cotacao: Mapped[CotacaoCompra] = relationship(back_populates="itens")

    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_produto.id"), nullable=False
    )
    produto: Mapped[Produto] = relationship(lazy="selectin")

    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precos: Mapped[list[CotacaoCompraPreco]] = relationship(
        back_populates="item",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CotacaoCompraPreco.fornecedor_id",
    )


class CotacaoCompraPreco(Base):
    __tablename__ = "inventory_cotacomprecpreco"
    __table_args__ = (
        UniqueConstraint("item_id", "fornecedor_id", name="uniq_item_fornecedor"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cotacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_cotacaocompra.id"), nullable=False
    )
    cotacao: Mapped[CotacaoCompra] = relationship(lazy="selectin")

    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_cotacaocompraitem.id"), nullable=False
    )
    item: Mapped[CotacaoCompraItem] = relationship(back_populates="precos")

    fornecedor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_fornecedor.id"), nullable=False
    )
    fornecedor: Mapped[Fornecedor] = relationship(lazy="selectin")

    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))


class CotacaoCompraImpressao(Base):
    __tablename__ = "inventory_cotacaocompraimpressao"

    ORIGINAL = "ORIGINAL"
    SEGUNDA_VIA = "2A_VIA"
    VIA_CHOICES = (ORIGINAL, SEGUNDA_VIA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cotacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_cotacaocompra.id"), nullable=False
    )
    cotacao: Mapped[CotacaoCompra] = relationship(lazy="selectin")

    impresso_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    impresso_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    impresso_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[impresso_por_id])
    via: Mapped[str] = mapped_column(String(20), default=ORIGINAL)


class OrdemCompra(Base):
    """Ordem de compra gerada na aprovação de cotação.

    Campos Twilio (twilio_sid, erro_envio) REMOVIDOS - integração WhatsApp adiada.
    """

    __tablename__ = "inventory_ordemcompra"

    PENDENTE = "PENDENTE"
    ENVIADA = "ENVIADA"
    FALHA = "FALHA"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True, default="")

    cotacao_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_cotacaocompra.id"), nullable=False, unique=True
    )
    cotacao: Mapped[CotacaoCompra] = relationship(back_populates="ordem_compra")

    fornecedor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_fornecedor.id"), nullable=False
    )
    fornecedor: Mapped[Fornecedor] = relationship(lazy="selectin")

    mensagem: Mapped[str] = mapped_column(Text, default="")
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))

    # Sem Twilio: status_envio mantido mas não usado para envio WhatsApp.
    status_envio: Mapped[str] = mapped_column(String(12), default=PENDENTE)
    enviada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())