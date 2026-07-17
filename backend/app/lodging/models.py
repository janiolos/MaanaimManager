"""Modelos do módulo lodging - espelham tabelas Django `lodging_*`.

- lodging_chale
- lodging_reservachale
- lodging_acaochale

ReservaChale e AcaoChale têm validações cross-tabela (conflito de período)
extraídas para os serviços (`ReservaChaleService.validar_periodo`,
`AcaoChaleService.validar_periodo`).
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
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.core.models import Evento, User
    from app.finance.models import ContaCaixa, LancamentoFinanceiro


class Chale(Base):
    """Chalé/cabana com capacidade e status."""

    __tablename__ = "lodging_chale"

    ATIVO = "ATIVO"
    MANUTENCAO = "MANUTENCAO"
    INATIVO = "INATIVO"
    STATUS_CHOICES = (ATIVO, MANUTENCAO, INATIVO)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    capacidade: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default=ATIVO)
    acessivel_cadeirante: Mapped[bool] = mapped_column(Boolean, default=False)
    observacoes: Mapped[str] = mapped_column(Text, default="")

    acoes: Mapped[list[AcaoChale]] = relationship(
        back_populates="chale", lazy="selectin"
    )


class ReservaChale(Base):
    """Reserva de chalé atrelada a um Evento.

    7 regras de validação (extraídas do `clean()` Django para o serviço):
    1. período obrigatório (data_entrada + data_saida)
    2. data_saida > data_entrada
    3. detalhes_necessidade_especial obrigatório se possui_necessidade_especial
    4. total_hospedes <= chale.capacidade
    5. chale.status == ATIVO
    6. sem conflito com outra ReservaChale ativa no mesmo período
    7. sem conflito com AcaoChale ativa (bloqueio/manutenção) no mesmo período

    Se `pago=True` + `forma_pagamento` + `conta` preenchidos, serviço cria
    LancamentoFinanceiro RECEITA categoria "Hospedagem".
    """

    __tablename__ = "lodging_reservachale"

    PRE_RESERVA = "PRE_RESERVA"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = (PRE_RESERVA, CONFIRMADA, CANCELADA)
    STATUS_ATIVOS = (PRE_RESERVA, CONFIRMADA)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"))
    evento: Mapped[Evento] = relationship(lazy="selectin")

    chale_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lodging_chale.id"))
    chale: Mapped[Chale] = relationship(lazy="selectin", back_populates=None)

    data_entrada: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_saida: Mapped[date | None] = mapped_column(Date, nullable=True)

    responsavel_nome: Mapped[str] = mapped_column(String(120))
    qtd_pessoas: Mapped[int] = mapped_column(Integer)
    qtd_criancas: Mapped[int] = mapped_column(Integer, default=0)
    idades_criancas: Mapped[str] = mapped_column(String(120), default="")
    possui_necessidade_especial: Mapped[bool] = mapped_column(Boolean, default=False)
    detalhes_necessidade_especial: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[str] = mapped_column(String(20), default=PRE_RESERVA)
    valor_adicional: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    pago: Mapped[bool] = mapped_column(Boolean, default=False)
    forma_pagamento: Mapped[str] = mapped_column(String(10), default="")
    conta_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("finance_contacaixa.id"), nullable=True
    )
    conta: Mapped[ContaCaixa | None] = relationship(lazy="selectin")

    lancamento_financeiro_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("finance_lancamentofinanceiro.id"), nullable=True
    )
    lancamento_financeiro: Mapped[LancamentoFinanceiro | None] = relationship(lazy="selectin")

    observacoes: Mapped[str] = mapped_column(Text, default="")

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    atualizado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    atualizado_por: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[atualizado_por_id])
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AcaoChale(Base):
    """Ação de chalé (bloqueio ou manutenção) por período.

    Validações em `AcaoChaleService.validar_periodo`:
    1. data_fim > data_inicio
    2. sem ReservaChale ativa em sobreposição
    3. sem outra AcaoChale ativa em sobreposição (excluindo self)
    """

    __tablename__ = "lodging_acaochale"

    BLOQUEIO = "BLOQUEIO"
    MANUTENCAO = "MANUTENCAO"
    TIPO_CHOICES = (BLOQUEIO, MANUTENCAO)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    evento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("core_evento.id"))
    evento: Mapped[Evento] = relationship(lazy="selectin")

    chale_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lodging_chale.id"))
    chale: Mapped[Chale] = relationship(back_populates="acoes", lazy="selectin")

    tipo: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(120))
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)
    descricao: Mapped[str] = mapped_column(Text, default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    criado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auth_user.id"))
    criado_por: Mapped[User] = relationship(lazy="selectin", foreign_keys=[criado_por_id])
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    atualizado_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auth_user.id"), nullable=True
    )
    atualizado_por: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[atualizado_por_id])
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )