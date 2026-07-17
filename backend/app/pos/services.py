"""Services do módulo POS (PDV).

VendaService - cria venda, valida estoque, baixa sub-estoque, registra pagamentos.
EntradaLocalService - entrada de mercadoria em sub-estoque local.
"""

from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import ConfiguracaoEvento, Evento
from app.inventory.services import EstoqueService
from app.pos.finance_integration import POSFinanceIntegration
from app.pos.models import (
    EntradaEstoqueLocal,
    ItemVendaMobile,
    LocalVenda,
    PagamentoVenda,
    ProdutoLocal,
    TransferenciaEstoqueLocal,
    VendaMobile,
)
from app.pos.schemas import (
    EntradaEstoqueLocalCreate,
    ItemVendaIn,
    TransferenciaEstoqueLocalCreate,
    VendaCreate,
)


class VendaService:
    """Cria e confirma vendas do PDV."""

    @staticmethod
    async def _validar_evento_para_venda(session: AsyncSession, evento_id: int) -> None:
        evento = await session.get(Evento, evento_id)
        if evento is None:
            raise ValueError("Evento não encontrado")
        if evento.fechado or evento.status == Evento.ENCERRADO:
            raise ValueError("Evento encerrado - vendas bloqueadas")
        config = await session.execute(
            select(ConfiguracaoEvento).where(ConfiguracaoEvento.evento_id == evento_id)
        )
        config = config.scalar_one_or_none()
        if config is not None and not config.permite_vendas_pos:
            raise ValueError("Vendas bloqueadas para este evento")

    @staticmethod
    async def _validar_local(session: AsyncSession, local_id: int | None) -> LocalVenda:
        if local_id is None:
            raise ValueError("Local de venda obrigatório")
        local = (
            await session.execute(
                select(LocalVenda).where(
                    LocalVenda.id == local_id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if local is None:
            raise ValueError("Local de venda não encontrado")
        if not local.ativo or not local.modulo_pdv:
            raise ValueError("PDV inativo para este local")
        if not local.caixa_aberto:
            raise ValueError("Caixa fechado - abra o caixa antes de vender")
        return local

    @staticmethod
    async def criar(session: AsyncSession, *, evento_id: int, vendedor_id: int, payload: VendaCreate) -> VendaMobile:
        await VendaService._validar_evento_para_venda(session, evento_id)
        local = await VendaService._validar_local(session, payload.local_id)

        existente = (
            await session.execute(
                select(VendaMobile)
                .options(selectinload(VendaMobile.itens), selectinload(VendaMobile.pagamentos))
                .where(VendaMobile.id_referencia == payload.id_referencia)
            )
        ).scalar_one_or_none()
        if existente is not None:
            if existente.evento_id != evento_id or existente.vendedor_id != vendedor_id:
                raise ValueError("Referência de venda já utilizada")
            return existente

        # 1. Calcular total dos itens
        total_itens = Decimal("0")
        itens_data: list[tuple[ItemVendaIn, ProdutoLocal, Decimal, Decimal]] = []
        produto_ids = [item.produto_local_id for item in payload.itens]
        if len(produto_ids) != len(set(produto_ids)):
            raise ValueError("O mesmo produto não pode aparecer mais de uma vez na venda")

        # Ordem estável de locks reduz a chance de deadlock entre caixas concorrentes.
        for item in sorted(payload.itens, key=lambda value: value.produto_local_id or 0):
            if item.produto_local_id is None:
                raise ValueError("Todos os itens devem estar vinculados ao estoque do local")
            pl = (
                await session.execute(
                    select(ProdutoLocal)
                    .options(selectinload(ProdutoLocal.produto), selectinload(ProdutoLocal.familia))
                    .where(
                        ProdutoLocal.id == item.produto_local_id,
                        ProdutoLocal.local_id == local.id,
                        ProdutoLocal.ativo.is_(True),
                    )
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if pl is None or not pl.produto.ativo:
                raise ValueError("Produto não pertence ao local ou está inativo")
            if item.desconto_perc > 0 and not local.permite_desconto:
                raise ValueError("Descontos não são permitidos neste local")
            if item.desconto_perc > Decimal(local.desconto_maximo_perc):
                raise ValueError(f"Desconto máximo permitido: {local.desconto_maximo_perc}%")
            qtd = Decimal(item.quantidade)
            if pl.estoque_atual < qtd:
                raise ValueError(
                    f"Estoque insuficiente: {pl.produto.nome} "
                    f"(disponível {pl.estoque_atual}, solicitado {qtd})"
                )
            preco_unitario = pl.preco_venda
            preco_bruto = preco_unitario * qtd
            desconto_valor = preco_bruto * (item.desconto_perc / Decimal("100"))
            total_item = preco_bruto - desconto_valor
            total_itens += total_item
            itens_data.append((item, pl, preco_unitario, total_item))

        # 2. Validar que pagamentos somam o total
        total_pagamentos = sum(p.valor for p in payload.pagamentos)
        if total_pagamentos != total_itens:
            raise ValueError(
                f"Pagamentos (R$ {total_pagamentos}) não conferem com o total (R$ {total_itens})"
            )

        # 3. Determinar forma_pagamento
        tipos_pagamento = {p.tipo for p in payload.pagamentos}
        if len(tipos_pagamento) > 1 and not local.permite_pagamento_misto:
            raise ValueError("Pagamento misto não é permitido neste local")
        if len(tipos_pagamento) == 1:
            forma_pagamento = tipos_pagamento.pop()
        else:
            forma_pagamento = "MISTO"

        # 4. Criar VendaMobile
        venda = VendaMobile(
            id_referencia=payload.id_referencia,
            evento_id=evento_id,
            local_id=payload.local_id,
            vendedor_id=vendedor_id,
            total=total_itens,
            forma_pagamento=forma_pagamento,
            data_hora=datetime.now(UTC),
        )
        session.add(venda)
        await session.flush()  # para obter venda.id

        # 5. Criar itens e baixar estoque
        for item, pl, preco_unitario, total_item in itens_data:
            item_venda = ItemVendaMobile(
                venda_id=venda.id,
                produto_local_id=item.produto_local_id,
                nome_produto=pl.produto.nome,
                codigo_produto=pl.produto.sku,
                familia_produto=pl.familia.nome if pl.familia else "",
                quantidade=item.quantidade,
                preco_unitario=preco_unitario,
                desconto_perc=item.desconto_perc,
                total_item=total_item,
            )
            session.add(item_venda)

            # Baixar sub-estoque local
            pl.estoque_atual -= Decimal(item.quantidade)

        # 6. Registrar pagamentos
        for pgto in payload.pagamentos:
            session.add(PagamentoVenda(venda_id=venda.id, tipo=pgto.tipo, valor=pgto.valor))

        # 7. Criar lançamentos financeiros de receita
        local_nome = "PDV"
        if payload.local_id:
            local_obj = await session.get(LocalVenda, payload.local_id)
            if local_obj:
                local_nome = local_obj.nome
        await POSFinanceIntegration.criar_lancamentos_da_venda(
            session, venda, payload.pagamentos, local_nome, vendedor_id
        )

        await session.flush()
        await session.refresh(venda)
        return venda


class EntradaLocalService:
    """Registra entrada de mercadoria em sub-estoque local."""

    @staticmethod
    async def _validar_evento_para_entrada(
        session: AsyncSession, evento_id: int, produto_local_id: int
    ) -> None:
        pl = await session.get(ProdutoLocal, produto_local_id)
        if pl is None:
            raise ValueError("ProdutoLocal não encontrado")
        local = await session.get(LocalVenda, pl.local_id)
        if local is None:
            raise ValueError("Local de venda não encontrado")
        if not local.ativo:
            raise ValueError("Local de venda inativo")
        evento = await session.get(Evento, evento_id)
        if evento is None:
            raise ValueError("Evento não encontrado")
        if evento.fechado or evento.status == Evento.ENCERRADO:
            raise ValueError("Evento encerrado - entradas de estoque bloqueadas")
        config = await session.execute(
            select(ConfiguracaoEvento).where(ConfiguracaoEvento.evento_id == evento_id)
        )
        config = config.scalar_one_or_none()
        if config is not None and not config.permite_edicao_estoque_pos:
            raise ValueError("Entradas de estoque bloqueadas para este evento")

    @staticmethod
    async def criar(
        session: AsyncSession, *, evento_id: int, user_id: int, payload: EntradaEstoqueLocalCreate
    ) -> EntradaEstoqueLocal:
        await EntradaLocalService._validar_evento_para_entrada(session, evento_id, payload.produto_local_id)

        pl = await session.get(ProdutoLocal, payload.produto_local_id)
        if pl is None:
            raise ValueError(f"ProdutoLocal id={payload.produto_local_id} não encontrado")

        entrada = EntradaEstoqueLocal(
            produto_local_id=payload.produto_local_id,
            quantidade=payload.quantidade,
            preco_custo=payload.preco_custo,
            preco_venda=payload.preco_venda,
            data=payload.data,
            observacao=payload.observacao,
            criado_por_id=user_id,
        )
        session.add(entrada)

        # Atualizar sub-estoque
        pl.estoque_atual += payload.quantidade
        if payload.preco_venda > 0:
            pl.preco_venda = payload.preco_venda

        await session.flush()
        await session.refresh(entrada)
        return entrada


class TransferenciaEstoqueLocalService:
    """Move saldo do catálogo central para um subestoque, com locks nas duas linhas."""

    @staticmethod
    async def criar(
        session: AsyncSession,
        *,
        evento_id: int,
        user_id: int,
        payload: TransferenciaEstoqueLocalCreate,
    ) -> TransferenciaEstoqueLocal:
        pl = (
            await session.execute(
                select(ProdutoLocal)
                .join(LocalVenda, ProdutoLocal.local_id == LocalVenda.id)
                .where(
                    ProdutoLocal.id == payload.produto_local_id,
                    LocalVenda.ativo.is_(True),
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if pl is None:
            raise ValueError("Produto local não encontrado ou local inativo")

        await EntradaLocalService._validar_evento_para_entrada(session, evento_id, pl.id)
        produto = await EstoqueService.lock_produto(session, pl.produto_id)
        custo_unitario = produto.custo_medio_atual
        await EstoqueService.aplicar_saida(session, produto, payload.quantidade)
        pl.estoque_atual += payload.quantidade

        transferencia = TransferenciaEstoqueLocal(
            produto_local_id=pl.id,
            quantidade=payload.quantidade,
            custo_unitario=custo_unitario,
            data=payload.data,
            observacao=payload.observacao,
            criado_por_id=user_id,
        )
        session.add(transferencia)
        await session.flush()
        await session.refresh(transferencia)
        return transferencia
