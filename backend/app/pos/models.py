"""Models SQLAlchemy do módulo POS (PDV).

Espelha tabelas Django: pos_localvenda, pos_familiavenda, pos_produtolocal,
pos_entradaestquelocal, pos_vendamobile, pos_pagamentovenda, pos_itemvendamobile.

Mantém nomes de tabela Django para compatibilidade com dados existentes.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Evento, User
from app.db.base import Base
from app.inventory.models import Produto


# ---------------------------------------------------------------------------
# Estrutura perene do PDV
# ---------------------------------------------------------------------------


class LocalVenda(Base):
    __tablename__ = "pos_localvenda"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core_evento.id", ondelete="SET NULL"), nullable=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    modulo_dashboard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    modulo_pdv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    modulo_vendas: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    modulo_produtos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    modulo_estoque: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permite_desconto: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    desconto_maximo_perc: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    permite_pagamento_misto: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deposito_interno: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    caixa_aberto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    caixa_aberto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    caixa_aberto_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    caixa_aberto_por: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[caixa_aberto_por_id])
    caixa_atual_turno_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_turnocaixa.id", ondelete="SET NULL"), nullable=True
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evento: Mapped[Evento | None] = relationship(lazy="selectin")
    familias: Mapped[list["FamiliaVenda"]] = relationship(back_populates="local", lazy="selectin")
    produtos: Mapped[list["ProdutoLocal"]] = relationship(back_populates="local", lazy="selectin")


class TurnoCaixa(Base):
    __tablename__ = "pos_turnocaixa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    local_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_localvenda.id", ondelete="CASCADE"), nullable=False
    )
    evento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core_evento.id", ondelete="SET NULL"), nullable=True
    )
    aberto_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aberto_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"), nullable=False)
    fechado_por_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("auth_user.id"), nullable=True)
    valor_abertura: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    valor_fechamento: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    fechado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relatorio_pdf: Mapped[str | None] = mapped_column(String(500), nullable=True)

    local: Mapped["LocalVenda"] = relationship(lazy="selectin", foreign_keys=[local_id])
    aberto_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[aberto_por_id])
    fechado_por: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[fechado_por_id])


class FamiliaVenda(Base):
    __tablename__ = "pos_familiavenda"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    local_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_localvenda.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)

    __table_args__ = (
        UniqueConstraint("local_id", "nome", name="uniq_familia_local_nome"),
    )

    local: Mapped["LocalVenda"] = relationship(back_populates="familias", lazy="selectin")
    produtos: Mapped[list["ProdutoLocal"]] = relationship(back_populates="familia", lazy="selectin")


class ProdutoLocal(Base):
    __tablename__ = "pos_produtolocal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_produto.id", ondelete="CASCADE"), nullable=False
    )
    local_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_localvenda.id", ondelete="CASCADE"), nullable=False
    )
    familia_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_familiavenda.id", ondelete="SET NULL"), nullable=True
    )

    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    estoque_atual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    estoque_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    ponto_reabastecimento: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    estoque_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("produto_id", "local_id", name="uniq_produto_local"),
    )

    local: Mapped["LocalVenda"] = relationship(back_populates="produtos", lazy="selectin")
    familia: Mapped["FamiliaVenda | None"] = relationship(back_populates="produtos", lazy="selectin")
    produto: Mapped[Produto] = relationship(lazy="selectin")


class EntradaEstoqueLocal(Base):
    __tablename__ = "pos_entradaestquelocal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_local_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_produtolocal.id", ondelete="CASCADE"), nullable=False
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    preco_custo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    observacao: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    criado_por_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_user.id", ondelete="PROTECT"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    produto_local: Mapped["ProdutoLocal"] = relationship(lazy="selectin")
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])


class TransferenciaEstoqueLocal(Base):
    """Transferência atômica do estoque central para um ponto de venda."""

    __tablename__ = "pos_transferenciaestoquelocal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_local_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_produtolocal.id", ondelete="RESTRICT"), nullable=False
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    observacao: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    criado_por_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_user.id", ondelete="RESTRICT"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    produto_local: Mapped["ProdutoLocal"] = relationship(lazy="selectin")
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])


# ---------------------------------------------------------------------------
# Vendas do PDV
# ---------------------------------------------------------------------------


class VendaMobile(Base):
    __tablename__ = "pos_vendamobile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_referencia: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    evento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core_evento.id", ondelete="PROTECT"), nullable=False
    )
    local_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_localvenda.id", ondelete="PROTECT"), nullable=True
    )
    vendedor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_user.id", ondelete="PROTECT"), nullable=False
    )
    data_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(20), default="MISTO", nullable=False)

    vendedor: Mapped[User] = relationship(lazy="selectin", foreign_keys=[vendedor_id])
    local: Mapped["LocalVenda | None"] = relationship(lazy="selectin")
    itens: Mapped[list["ItemVendaMobile"]] = relationship(back_populates="venda", lazy="selectin")
    pagamentos: Mapped[list["PagamentoVenda"]] = relationship(back_populates="venda", lazy="selectin")
    turno_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_turnocaixa.id", ondelete="SET NULL"), nullable=True
    )
    turno: Mapped[TurnoCaixa | None] = relationship(lazy="selectin")


class PagamentoVenda(Base):
    __tablename__ = "pos_pagamentovenda"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venda_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_vendamobile.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    venda: Mapped["VendaMobile"] = relationship(back_populates="pagamentos")


class ItemVendaMobile(Base):
    __tablename__ = "pos_itemvendamobile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venda_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pos_vendamobile.id", ondelete="CASCADE"), nullable=False
    )
    produto_local_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pos_produtolocal.id", ondelete="PROTECT"), nullable=True
    )
    nome_produto: Mapped[str] = mapped_column(String(140), default="", nullable=False)
    codigo_produto: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    familia_produto: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desconto_perc: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    total_item: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    venda: Mapped["VendaMobile"] = relationship(back_populates="itens")
    produto_local: Mapped["ProdutoLocal | None"] = relationship(lazy="selectin")
