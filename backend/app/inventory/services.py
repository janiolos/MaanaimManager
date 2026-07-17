"""Serviços do módulo inventory.

Críticos:
- `DocumentosService.proximo_numero` - gera números sequenciais REQ/COT/OC-YYYY-NNNNNN
- `EstoqueService.registrar_entrada / aplicar_saida` - média ponderada + lock
- `RequisicaoService.finalizar` - atomic baixa estoque por item com snapshot
- `CotacaoService.aprovar` - cria LancamentoFinanceiro DESPESA + OrdemCompra + entrada em estoque
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.models import LancamentoFinanceiro
from app.inventory.models import (
    CotacaoCompra,
    CotacaoCompraItem,
    CotacaoCompraPreco,
    EntradaEstoque,
    Fornecedor,
    OrdemCompra,
    Produto,
    RequisicaoSaida,
    RequisicaoSaidaItem,
)
from app.pos.models import LocalVenda, ProdutoLocal
from app.inventory.schemas import (
    CotacaoAprovarIn,
    CotacaoCreate,
    CotacaoUpdate,
    EntradaEstoqueCreate,
    FornecedorCreate,
    FornecedorUpdate,
    ProdutoCreate,
    ProdutoUpdate,
    RequisicaoCreate,
    RequisicaoUpdate,
)


# ============================ Documentos ============================


class DocumentosService:
    """Geração de números sequenciais por ano (REQ-YYYY-NNNNNN, COT-..., OC-...)."""

    @staticmethod
    async def proximo_numero(
        session: AsyncSession,
        model: type,
        prefixo: str,
        *,
        ano: int | None = None,
    ) -> str:
        ano = ano or datetime.now(timezone.utc).year
        # MAX(numero) filtrando por prefixo+ano - dorme sobre lock transacional implícito
        stmt = select(func.max(model.numero)).where(model.numero.like(f"{prefixo}-{ano}-%"))
        atual = (await session.execute(stmt)).scalar_one()
        if not atual:
            seq = 1
        else:
            try:
                seq = int(atual.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        return f"{prefixo}-{ano}-{seq:06d}"


# ============================ Estoque (média ponderada) ============================


class EstoqueService:
    """Média ponderada de custo + locks `SELECT FOR UPDATE`.

    Métodos NÃO persistem; caller faz flush/commit dentro da transação.
    """

    @staticmethod
    async def registrar_entrada(
        session: AsyncSession,
        produto: Produto,
        quantidade: Decimal,
        custo_unitario: Decimal,
    ) -> None:
        """Equivalente a `Produto.registrar_entrada` do Django."""
        if quantidade <= 0:
            raise ValueError("quantidade deve ser > 0")
        if custo_unitario < 0:
            raise ValueError("custo_unitario não pode ser negativo")

        novo_valor = produto.estoque_atual * produto.custo_medio_atual + quantidade * custo_unitario
        novo_estoque = produto.estoque_atual + quantidade
        produto.estoque_atual = novo_estoque
        produto.valor_estoque_atual = novo_valor
        produto.custo_medio_atual = (
            novo_valor / novo_estoque if novo_estoque > 0 else Decimal("0.0000")
        )
        await session.flush()

    @staticmethod
    async def aplicar_saida(
        session: AsyncSession,
        produto: Produto,
        quantidade: Decimal,
    ) -> Decimal:
        """Equivalente a `Produto.aplicar_saida` do Django. Retorna custo_total da saída."""
        if quantidade <= 0:
            raise ValueError("quantidade deve ser > 0")
        if quantidade > produto.estoque_atual:
            raise ValueError(
                f"Estoque insuficiente para {produto.nome}: necessidade {quantidade}, "
                f"disponível {produto.estoque_atual}"
            )
        custo_total = produto.custo_medio_atual * quantidade
        produto.estoque_atual -= quantidade
        produto.valor_estoque_atual -= custo_total
        if produto.estoque_atual > 0:
            produto.custo_medio_atual = produto.valor_estoque_atual / produto.estoque_atual
        else:
            produto.custo_medio_atual = Decimal("0.0000")
        await session.flush()
        return custo_total

    @staticmethod
    async def lock_produto(session: AsyncSession, produto_id: int) -> Produto:
        """SELECT ... FOR UPDATE - bloqueia a linha até commit/rollback."""
        stmt = select(Produto).where(Produto.id == produto_id).with_for_update()
        produto = (await session.execute(stmt)).scalar_one_or_none()
        if produto is None:
            raise NoResultFound(f"Produto {produto_id} não encontrado")
        return produto


# ============================ Produto ============================


class ProdutoService:
    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        ativo: bool | None = None,
        busca: str | None = None,
        categoria: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[Produto], int]:
        filters = []
        if ativo is not None:
            filters.append(Produto.ativo.is_(ativo))
        if busca:
            like = f"%{busca}%"
            filters.append((Produto.nome.ilike(like)) | (Produto.sku.ilike(like)))
        if categoria:
            filters.append(Produto.categoria == categoria)
        if status == "baixo":
            filters.append(Produto.estoque_atual < Produto.estoque_minimo)
        elif status == "reabastecer":
            filters.append(
                (Produto.estoque_reabastecimento > 0)
                & (Produto.estoque_atual < Produto.estoque_reabastecimento)
                & (Produto.estoque_atual >= Produto.estoque_minimo)
            )
        elif status == "acima":
            filters.append(
                (Produto.estoque_maximo > 0)
                & (Produto.estoque_atual > Produto.estoque_maximo)
            )

        total = (
            await session.execute(select(func.count()).select_from(Produto).where(*filters))
        ).scalar_one()

        stmt = (
            select(Produto)
            .where(*filters)
            .order_by(Produto.nome)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await session.execute(stmt)).scalars().all(), total

    @staticmethod
    async def get(session: AsyncSession, produto_id: int) -> Produto:
        p = await session.get(Produto, produto_id)
        if p is None:
            raise NoResultFound(f"Produto {produto_id} não encontrado")
        return p

    @staticmethod
    async def create(session: AsyncSession, payload: ProdutoCreate) -> Produto:
        p = Produto(**payload.model_dump())
        session.add(p)
        await session.flush()
        return p

    @staticmethod
    async def update(
        session: AsyncSession,
        produto: Produto,
        payload: ProdutoUpdate,
    ) -> Produto:
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(produto, k, v)
        await session.flush()
        return produto

    @staticmethod
    async def delete(session: AsyncSession, produto: Produto) -> None:
        await session.delete(produto)
        await session.flush()

    @staticmethod
    async def registrar_entrada(
        session: AsyncSession,
        payload: EntradaEstoqueCreate,
        user_id: int,
    ) -> tuple[Produto, EntradaEstoque]:
        """Workflow atômico: bloqueia produto, recalcula média ponderada, registra entrada."""
        async with session.begin_nested():
            produto = await session.get(Produto, payload.produto_id, with_for_update=True)
            if produto is None:
                raise NoResultFound("Produto não encontrado")
            await EstoqueService.registrar_entrada(
                session, produto, payload.quantidade, payload.custo_unitario
            )
            entrada = EntradaEstoque(
                produto_id=payload.produto_id,
                data=payload.data,
                quantidade=payload.quantidade,
                custo_unitario=payload.custo_unitario,
                documento=payload.documento,
                observacao=payload.observacao,
                criado_por_id=user_id,
            )
            session.add(entrada)
            await session.flush()
            return produto, entrada


# ============================ Requisicao ============================


class RequisicaoService:
    @staticmethod
    async def list(
        session: AsyncSession,
        evento_id: int,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[Sequence[RequisicaoSaida], int]:
        filters = [RequisicaoSaida.evento_id == evento_id]
        if status:
            filters.append(RequisicaoSaida.status == status)
        total = (
            await session.execute(
                select(func.count()).select_from(RequisicaoSaida).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(RequisicaoSaida)
            .where(*filters)
            .order_by(RequisicaoSaida.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await session.execute(stmt)).scalars().all(), total

    @staticmethod
    async def get(session: AsyncSession, requisicao_id: int) -> RequisicaoSaida:
        r = await session.get(RequisicaoSaida, requisicao_id)
        if r is None:
            raise NoResultFound(f"Requisição {requisicao_id} não encontrada")
        return r

    @staticmethod
    async def create(
        session: AsyncSession,
        evento_id: int,
        payload: RequisicaoCreate,
        user_id: int,
    ) -> RequisicaoSaida:
        numero = await DocumentosService.proximo_numero(session, RequisicaoSaida, "REQ")
        req = RequisicaoSaida(
            numero=numero,
            evento_id=evento_id,
            area=payload.area,
            observacao=payload.observacao,
            status=RequisicaoSaida.ABERTA,
            criado_por_id=user_id,
            itens=[
                RequisicaoSaidaItem(produto_id=i.produto_id, quantidade=i.quantidade)
                for i in payload.itens
            ],
        )
        session.add(req)
        await session.flush()
        return req

    @staticmethod
    async def update(
        session: AsyncSession,
        requisicao: RequisicaoSaida,
        payload: RequisicaoUpdate,
    ) -> RequisicaoSaida:
        if requisicao.status != RequisicaoSaida.ABERTA:
            raise ValueError("Apenas requisições ABERTA podem ser editadas")
        data = payload.model_dump(exclude_unset=True)
        novos_itens = data.pop("itens", None)
        for k, v in data.items():
            setattr(requisicao, k, v)
        if novos_itens is not None:
            # substitui itens
            for item in list(requisicao.itens):
                await session.delete(item)
            await session.flush()
            for i in novos_itens:
                requisicao.itens.append(
                    RequisicaoSaidaItem(produto_id=i["produto_id"], quantidade=i["quantidade"])
                )
        await session.flush()
        return requisicao

    @staticmethod
    async def finalizar(
        session: AsyncSession,
        requisicao: RequisicaoSaida,
        user_id: int,
    ) -> RequisicaoSaida:
        """Workflow crítico com locks atomic.

        1. valida status ABERTA
        2. lock na requisição
        3. lock no ProdutoLocal de origem (FOR UPDATE)
        4. valida estoque suficiente no local
        5. baixa estoque local com snapshot saldo_antes/depois/custos
        6. marca FINALIZADA
        """
        if requisicao.status != RequisicaoSaida.ABERTA:
            raise ValueError(f"Requisição {requisicao.numero} não está ABERTA")
        if not requisicao.itens:
            raise ValueError("Requisição sem itens")

        # lock e reload
        lock_stmt = (
            select(RequisicaoSaida)
            .where(RequisicaoSaida.id == requisicao.id)
            .with_for_update()
        )
        requisicao = (await session.execute(lock_stmt)).scalar_one()

        for item in requisicao.itens:
            if item.local_origem_id:
                pl = await session.get(ProdutoLocal, item.local_origem_id, with_for_update=True)
                if pl is None:
                    raise ValueError(f"Local de origem {item.local_origem_id} não encontrado")
                if pl.produto_id != item.produto_id:
                    raise ValueError("Local de origem não corresponde ao produto do item")
            else:
                # Busca depósito interno
                deposito = await session.execute(
                    select(LocalVenda).where(LocalVenda.is_deposito_interno.is_(True))
                )
                deposito = deposito.scalar_one_or_none()
                if deposito is None:
                    raise ValueError("Depósito interno não configurado")
                pl = await session.execute(
                    select(ProdutoLocal)
                    .where(
                        ProdutoLocal.local_id == deposito.id,
                        ProdutoLocal.produto_id == item.produto_id,
                    )
                    .with_for_update()
                )
                pl = pl.scalar_one_or_none()
                if pl is None:
                    raise ValueError(
                        f"Produto {item.produto.nome} não está cadastrado no depósito interno"
                    )

            if pl.estoque_atual < item.quantidade:
                raise ValueError(
                    f"Estoque insuficiente para {item.produto.nome} "
                    f"(necessário {item.quantidade}, disponível {pl.estoque_atual})"
                )

            item.saldo_antes = pl.estoque_atual
            item.custo_medio_unitario = item.produto.custo_medio_atual
            pl.estoque_atual -= item.quantidade
            item.custo_total = item.custo_medio_unitario * item.quantidade
            item.saldo_depois = pl.estoque_atual

        requisicao.status = RequisicaoSaida.FINALIZADA
        requisicao.finalizado_em = datetime.now(timezone.utc)
        requisicao.finalizado_por_id = user_id
        await session.flush()
        return requisicao

    @staticmethod
    async def cancelar(session: AsyncSession, requisicao: RequisicaoSaida) -> RequisicaoSaida:
        if requisicao.status == RequisicaoSaida.FINALIZADA:
            raise ValueError("Requisição já FINALIZADA não pode ser cancelada")
        requisicao.status = RequisicaoSaida.CANCELADA
        await session.flush()
        return requisicao


# ============================ Fornecedor ============================


class FornecedorService:
    @staticmethod
    async def list(session: AsyncSession, ativo: bool | None = None) -> Sequence[Fornecedor]:
        stmt = select(Fornecedor).order_by(Fornecedor.nome)
        if ativo is not None:
            stmt = stmt.where(Fornecedor.ativo.is_(ativo))
        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    async def get(session: AsyncSession, fid: int) -> Fornecedor:
        f = await session.get(Fornecedor, fid)
        if f is None:
            raise NoResultFound(f"Fornecedor {fid} não encontrado")
        return f

    @staticmethod
    async def create(session: AsyncSession, payload: FornecedorCreate) -> Fornecedor:
        # O schema legado nem sempre preserva o default de banco em `criado_em`.
        # Preenchemos explicitamente para não depender desse detalhe do DDL.
        f = Fornecedor(**payload.model_dump(), criado_em=datetime.now(timezone.utc))
        session.add(f)
        await session.flush()
        return f

    @staticmethod
    async def update(
        session: AsyncSession,
        fornecedor: Fornecedor,
        payload: FornecedorUpdate,
    ) -> Fornecedor:
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(fornecedor, k, v)
        await session.flush()
        return fornecedor

    @staticmethod
    async def delete(session: AsyncSession, fornecedor: Fornecedor) -> None:
        await session.delete(fornecedor)
        await session.flush()


# ============================ Cotacao ============================


class CotacaoService:
    @staticmethod
    async def list(
        session: AsyncSession,
        evento_id: int,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[Sequence[CotacaoCompra], int]:
        filters = [CotacaoCompra.evento_id == evento_id]
        if status:
            filters.append(CotacaoCompra.status == status)
        total = (
            await session.execute(
                select(func.count()).select_from(CotacaoCompra).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(CotacaoCompra)
            .where(*filters)
            .order_by(CotacaoCompra.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await session.execute(stmt)).scalars().all(), total

    @staticmethod
    async def get(session: AsyncSession, cotacao_id: int) -> CotacaoCompra:
        c = await session.get(CotacaoCompra, cotacao_id)
        if c is None:
            raise NoResultFound(f"Cotação {cotacao_id} não encontrada")
        return c

    @staticmethod
    async def create(
        session: AsyncSession,
        evento_id: int,
        payload: CotacaoCreate,
        user_id: int,
    ) -> CotacaoCompra:
        numero = await DocumentosService.proximo_numero(session, CotacaoCompra, "COT")
        cotacao = CotacaoCompra(
            numero=numero,
            evento_id=evento_id,
            observacao=payload.observacao,
            criado_por_id=user_id,
            status=CotacaoCompra.ABERTA,
        )
        for it in payload.itens:
            item = CotacaoCompraItem(produto_id=it.produto_id, quantidade=it.quantidade)
            for p in it.precos:
                # pre-calcula valor_total
                valor_total = p.valor_unitario * it.quantidade
                item.precos.append(
                    CotacaoCompraPreco(
                        fornecedor_id=p.fornecedor_id,
                        valor_unitario=p.valor_unitario,
                        valor_total=valor_total,
                    )
                )
            cotacao.itens.append(item)
        session.add(cotacao)
        await session.flush()
        return cotacao

    @staticmethod
    async def update(
        session: AsyncSession,
        cotacao: CotacaoCompra,
        payload: CotacaoUpdate,
        user_id: int,
    ) -> CotacaoCompra:
        if cotacao.status != CotacaoCompra.ABERTA:
            raise ValueError("Apenas cotações ABERTA podem ser editadas")
        data = payload.model_dump(exclude_unset=True)
        novos_itens = data.pop("itens", None)
        for k, v in data.items():
            setattr(cotacao, k, v)
        if novos_itens is not None:
            for item in list(cotacao.itens):
                await session.delete(item)
            await session.flush()
            for it in novos_itens:
                item = CotacaoCompraItem(produto_id=it["produto_id"], quantidade=it["quantidade"])
                for p in it["precos"]:
                    valor_total = Decimal(p["valor_unitario"]) * Decimal(it["quantidade"])
                    item.precos.append(
                        CotacaoCompraPreco(
                            fornecedor_id=p["fornecedor_id"],
                            valor_unitario=Decimal(p["valor_unitario"]),
                            valor_total=valor_total,
                        )
                    )
                cotacao.itens.append(item)
        await session.flush()
        return cotacao

    @staticmethod
    async def fechar(
        session: AsyncSession,
        cotacao: CotacaoCompra,
        user_id: int,
    ) -> CotacaoCompra:
        if cotacao.status != CotacaoCompra.ABERTA:
            raise ValueError(f"Cotação {cotacao.numero} não está ABERTA")
        if not cotacao.itens:
            raise ValueError("Cotação sem itens")
        # valida que todos os itens têm preços
        for item in cotacao.itens:
            if not item.precos:
                raise ValueError(f"Item {item.produto.sku} sem preços cadastrados")
        cotacao.status = CotacaoCompra.FECHADA
        cotacao.fechado_em = datetime.now(timezone.utc)
        cotacao.fechado_por_id = user_id
        await session.flush()
        return cotacao

    @staticmethod
    async def cancelar(session: AsyncSession, cotacao: CotacaoCompra) -> CotacaoCompra:
        if cotacao.status == CotacaoCompra.FECHADA and cotacao.ordem_compra is not None:
            raise ValueError("Cotação fechada com ordem de compra não pode ser cancelada")
        cotacao.status = CotacaoCompra.CANCELADA
        await session.flush()
        return cotacao

    @staticmethod
    async def aprovar(
        session: AsyncSession,
        cotacao: CotacaoCompra,
        payload: CotacaoAprovarIn,
        user_id: int,
    ) -> tuple[CotacaoCompra, LancamentoFinanceiro, OrdemCompra]:
        """Aprova cotação:
        1. valida status ABERTA
        2. valida fornecedor_id tem preços para todos os itens
        3. cria LancamentoFinanceiro DESPESA (categoria informada)
        4. cria OrdemCompra com mensagem
        5. registra EntradaEstoque + aplicar entrada em cada Produto (média ponderada, lock)
        6. marca cotação FECHADA + fornecedor_aprovado + valor_aprovado + aprovação
        """
        if cotacao.status != CotacaoCompra.ABERTA:
            raise ValueError(f"Cotação {cotacao.numero} não está ABERTA")
        if not cotacao.itens:
            raise ValueError("Cotação sem itens")

        from app.finance.models import CategoriaFinanceira, ContaCaixa
        cat = await session.get(CategoriaFinanceira, payload.categoria_despesa_id)
        if cat is None:
            raise ValueError("Categoria financeira não encontrada")
        if cat.tipo != LancamentoFinanceiro.DESPESA:
            raise ValueError("categoria_despesa_id precisa ser uma categoria de DESPESA")
        if await session.get(ContaCaixa, payload.conta_id) is None:
            raise ValueError("Conta de caixa não encontrada")
        fornecedor = await session.get(Fornecedor, payload.fornecedor_id)
        if fornecedor is None:
            raise ValueError("Fornecedor não encontrado")

        # valida preços para o fornecedor em todos os itens + soma valor_aprovado
        valor_total = Decimal("0.00")
        for item in cotacao.itens:
            preco = next(
                (p for p in item.precos if p.fornecedor_id == payload.fornecedor_id), None
            )
            if preco is None:
                raise ValueError(
                    f"Fornecedor {fornecedor.nome} não tem preço para item {item.produto.sku}"
                )
            valor_total += preco.valor_total

        # 1. LancamentoFinanceiro DESPESA
        lancamento = LancamentoFinanceiro(
            evento_id=cotacao.evento_id,
            tipo=LancamentoFinanceiro.DESPESA,
            categoria_id=payload.categoria_despesa_id,
            conta_id=payload.conta_id,
            data=payload.data,
            descricao=f"Cotação {cotacao.numero} - {fornecedor.nome}",
            valor=valor_total,
            forma_pagamento=payload.forma_pagamento,
            criado_por_id=user_id,
            setor_origem="inventory",
            pessoa=fornecedor.nome,
        )
        session.add(lancamento)
        await session.flush()

        # 2. OrdemCompra (sem Twilio)
        numero_oc = await DocumentosService.proximo_numero(session, OrdemCompra, "OC")
        ordem = OrdemCompra(
            numero=numero_oc,
            cotacao_id=cotacao.id,
            fornecedor_id=fornecedor.id,
            mensagem=payload.observacao or f"OC {numero_oc} referente a cotação {cotacao.numero}",
            valor_total=valor_total,
            status_envio=OrdemCompra.PENDENTE,
            criado_por_id=user_id,
        )
        session.add(ordem)
        await session.flush()

        # 3. Entrada em estoque por item (lock + média ponderada)
        for item in cotacao.itens:
            produto = await EstoqueService.lock_produto(session, item.produto_id)
            preco = next(
                (p for p in item.precos if p.fornecedor_id == payload.fornecedor_id), None
            )
            assert preco is not None  # garantido acima
            await EstoqueService.registrar_entrada(
                session, produto, item.quantidade, preco.valor_unitario
            )
            entrada = EntradaEstoque(
                produto_id=item.produto_id,
                data=payload.data,
                quantidade=item.quantidade,
                custo_unitario=preco.valor_unitario,
                documento=cotacao.numero,
                observacao=f"OC {numero_oc}",
                criado_por_id=user_id,
            )
            session.add(entrada)
        await session.flush()

        # 4. fecha cotação
        cotacao.status = CotacaoCompra.FECHADA
        cotacao.fornecedor_aprovado_id = fornecedor.id
        cotacao.valor_aprovado = valor_total
        cotacao.aprovado_em = datetime.now(timezone.utc)
        cotacao.aprovado_por_id = user_id
        cotacao.fechado_em = cotacao.aprovado_em
        cotacao.fechado_por_id = user_id
        cotacao.lancamento_financeiro_id = lancamento.id
        await session.flush()

        return cotacao, lancamento, ordem


# ============================ Dashboard ============================


class InventoryDashboardService:
    @staticmethod
    async def dashboard(session: AsyncSession, evento_id: int) -> dict[str, object]:
        total_produtos = (
            await session.execute(select(func.count()).select_from(Produto))
        ).scalar_one()
        produtos_ativos = (
            await session.execute(
                select(func.count()).select_from(Produto).where(Produto.ativo.is_(True))
            )
        ).scalar_one()

        # estoque baixo: atual < minimo; reabastecer: atual < reabastecimento (e >= minimo)
        baixo = (
            await session.execute(
                select(func.count())
                .select_from(Produto)
                .where(Produto.ativo.is_(True), Produto.estoque_atual < Produto.estoque_minimo)
            )
        ).scalar_one()
        reabast = (
            await session.execute(
                select(func.count())
                .select_from(Produto)
                .where(
                    Produto.ativo.is_(True),
                    Produto.estoque_atual < Produto.estoque_reabastecimento,
                    Produto.estoque_atual >= Produto.estoque_minimo,
                )
            )
        ).scalar_one()

        valor_total = (
            await session.execute(select(func.sum(Produto.valor_estoque_atual)))
        ).scalar_one() or Decimal("0.00")

        req_abertas = (
            await session.execute(
                select(func.count())
                .select_from(RequisicaoSaida)
                .where(
                    RequisicaoSaida.evento_id == evento_id,
                    RequisicaoSaida.status == RequisicaoSaida.ABERTA,
                )
            )
        ).scalar_one()
        cot_abertas = (
            await session.execute(
                select(func.count())
                .select_from(CotacaoCompra)
                .where(
                    CotacaoCompra.evento_id == evento_id,
                    CotacaoCompra.status == CotacaoCompra.ABERTA,
                )
            )
        ).scalar_one()

        return {
            "total_produtos": total_produtos,
            "produtos_ativos": produtos_ativos,
            "estoque_baixo": baixo,
            "estoque_reabastecer": reabast,
            "valor_total_estoque": valor_total,
            "requisicoes_abertas": req_abertas,
            "cotacoes_abertas": cot_abertas,
        }
