"""Integração do módulo POS com Finance.

Cria LancamentoFinanceiro de RECEITA automaticamente para cada venda do PDV.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro
from app.pos.models import VendaMobile
from app.pos.schemas import PagamentoIn


class POSFinanceIntegration:
    """Helper para gerar lançamentos financeiros a partir de vendas do PDV."""

    CATEGORIA_NOME = "Vendas PDV"
    CONTA_NOME = "Caixa PDV"

    # Mapeamento de formas do PDV → formas do financeiro
    FORMA_MAP = {
        "DINHEIRO": LancamentoFinanceiro.DINHEIRO,
        "PIX": LancamentoFinanceiro.PIX,
        "DÉBITO": LancamentoFinanceiro.CARTAO,
        "CRÉDITO": LancamentoFinanceiro.CARTAO,
        "MISTO": LancamentoFinanceiro.OUTRO,
    }

    @staticmethod
    async def _get_or_create_categoria_receita(session: AsyncSession) -> CategoriaFinanceira:
        stmt = select(CategoriaFinanceira).where(
            CategoriaFinanceira.tipo == CategoriaFinanceira.RECEITA,
            CategoriaFinanceira.nome == POSFinanceIntegration.CATEGORIA_NOME,
        )
        result = await session.execute(stmt)
        cat = result.scalars().first()
        if cat is None:
            # tenta qualquer categoria de receita
            stmt2 = select(CategoriaFinanceira).where(
                CategoriaFinanceira.tipo == CategoriaFinanceira.RECEITA
            ).order_by(CategoriaFinanceira.id)
            result2 = await session.execute(stmt2)
            cat = result2.scalars().first()
        if cat is None:
            cat = CategoriaFinanceira(nome=POSFinanceIntegration.CATEGORIA_NOME, tipo=CategoriaFinanceira.RECEITA)
            session.add(cat)
            await session.flush()
        return cat

    @staticmethod
    async def _get_or_create_conta_caixa(session: AsyncSession) -> ContaCaixa:
        stmt = select(ContaCaixa).where(
            ContaCaixa.nome == POSFinanceIntegration.CONTA_NOME,
            ContaCaixa.ativo.is_(True),
        )
        result = await session.execute(stmt)
        conta = result.scalars().first()
        if conta is None:
            stmt2 = select(ContaCaixa).where(ContaCaixa.ativo.is_(True)).order_by(ContaCaixa.id)
            result2 = await session.execute(stmt2)
            conta = result2.scalars().first()
        if conta is None:
            conta = ContaCaixa(nome=POSFinanceIntegration.CONTA_NOME, ativo=True)
            session.add(conta)
            await session.flush()
        return conta

    @staticmethod
    async def criar_lancamentos_da_venda(
        session: AsyncSession,
        venda: VendaMobile,
        pagamentos: list[PagamentoIn],
        local_nome: str,
        user_id: int,
    ) -> list[LancamentoFinanceiro]:
        """Cria um ou mais LancamentoFinanceiro de RECEITA para a venda.

        Agrupa pagamentos pela forma de pagamento mapeada e cria um lançamento
        por grupo.  Se todos os pagamentos são da mesma forma, cria um único
        lançamento.
        """
        categoria = await POSFinanceIntegration._get_or_create_categoria_receita(session)
        conta = await POSFinanceIntegration._get_or_create_conta_caixa(session)

        # Agrupa pagamentos por forma mapeada
        grupos: dict[str, Decimal] = {}
        for pgto in pagamentos:
            forma = POSFinanceIntegration.FORMA_MAP.get(pgto.tipo, LancamentoFinanceiro.OUTRO)
            grupos[forma] = grupos.get(forma, Decimal("0")) + Decimal(str(pgto.valor))

        lancamentos: list[LancamentoFinanceiro] = []
        hoje = date.today()

        for forma, valor in grupos.items():
            desc = (
                f"Venda PDV #{venda.id_referencia[:8]} — "
                f"Local: {local_nome} — "
                f"Forma: {forma}"
            )
            lanc = LancamentoFinanceiro(
                evento_id=venda.evento_id,
                tipo=LancamentoFinanceiro.RECEITA,
                categoria_id=categoria.id,
                conta_id=conta.id,
                data=hoje,
                descricao=desc,
                valor=valor,
                forma_pagamento=forma,
                criado_por_id=user_id,
                setor_origem="pos",
                pessoa=local_nome,
            )
            session.add(lanc)
            lancamentos.append(lanc)

        await session.flush()
        return lancamentos
