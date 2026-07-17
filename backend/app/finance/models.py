"""Modelos do módulo finance - espelham tabelas Django `finance_*`.

Tabelas:
- finance_categoriafinanceira
- finance_contacaixa
- finance_lancamentofinanceiro
- finance_anexolancamento
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.core.models import Evento, User


class CategoriaFinanceira(Base):
    __tablename__ = "finance_categoriafinanceira"

    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    TIPOS = (RECEITA, DESPESA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[str] = mapped_column(String(10))

    lancamentos: Mapped[list[LancamentoFinanceiro]] = relationship(
        back_populates="categoria", lazy="selectin"
    )


class ContaCaixa(Base):
    __tablename__ = "finance_contacaixa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    lancamentos: Mapped[list[LancamentoFinanceiro]] = relationship(
        back_populates="conta", lazy="selectin"
    )


class LancamentoFinanceiro(Base):
    __tablename__ = "finance_lancamentofinanceiro"

    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    TIPOS = (RECEITA, DESPESA)

    DINHEIRO = "DINHEIRO"
    PIX = "PIX"
    CARTAO = "CARTAO"
    OUTRO = "OUTRO"
    FORMAS_PAGAMENTO = (DINHEIRO, PIX, CARTAO, OUTRO)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"), nullable=False)
    evento: Mapped[Evento] = relationship(lazy="selectin")

    tipo: Mapped[str] = mapped_column(String(10))
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("finance_categoriafinanceira.id"), nullable=False
    )
    categoria: Mapped[CategoriaFinanceira] = relationship(back_populates="lancamentos", lazy="selectin")

    conta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("finance_contacaixa.id"), nullable=False
    )
    conta: Mapped[ContaCaixa] = relationship(back_populates="lancamentos", lazy="selectin")

    data: Mapped[date] = mapped_column(Date)
    descricao: Mapped[str] = mapped_column(String(255))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    forma_pagamento: Mapped[str] = mapped_column(String(10))

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"), nullable=False)
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])

    setor_origem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pessoa: Mapped[str | None] = mapped_column(String(150), nullable=True)
    assinatura_b64: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)

    atualizado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    atualizado_por: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[atualizado_por_id])

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, onupdate=func.now()
    )

    anexos: Mapped[list[AnexoLancamento]] = relationship(
        back_populates="lancamento", lazy="selectin", cascade="all, delete-orphan"
    )


class AnexoLancamento(Base):
    __tablename__ = "finance_anexolancamento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lancamento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("finance_lancamentofinanceiro.id"), nullable=False
    )
    lancamento: Mapped[LancamentoFinanceiro] = relationship(back_populates="anexos")

    arquivo: Mapped[str] = mapped_column(String(500))  # caminho relativo em MEDIA_ROOT
    descricao: Mapped[str] = mapped_column(String(255), default="")

    enviado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"), nullable=False)
    enviado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[enviado_por_id])

    enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow)