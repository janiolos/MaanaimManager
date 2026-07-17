"""Serviços do módulo finance - extraídos de apps/finance/views/* do Django."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.models import (
    CategoriaFinanceira,
    ContaCaixa,
    LancamentoFinanceiro,
)
from app.finance.schemas import LancamentoCreate, LancamentoUpdate
from app.core.models import Evento


class CategoriaService:
    @staticmethod
    async def list(session: AsyncSession, tipo: str | None = None) -> Sequence[CategoriaFinanceira]:
        stmt = select(CategoriaFinanceira).order_by(CategoriaFinanceira.nome)
        if tipo:
            stmt = stmt.where(CategoriaFinanceira.tipo == tipo)
        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    async def get(session: AsyncSession, cat_id: int) -> CategoriaFinanceira:
        cat = await session.get(CategoriaFinanceira, cat_id)
        if cat is None:
            raise NoResultFound(f"Categoria {cat_id} não encontrada")
        return cat

    @staticmethod
    async def create(session: AsyncSession, nome: str, tipo: str) -> CategoriaFinanceira:
        cat = CategoriaFinanceira(nome=nome, tipo=tipo)
        session.add(cat)
        await session.flush()
        return cat

    @staticmethod
    async def update(
        session: AsyncSession,
        cat: CategoriaFinanceira,
        payload: dict,
    ) -> CategoriaFinanceira:
        for k, v in payload.items():
            if v is not None:
                setattr(cat, k, v)
        await session.flush()
        return cat

    @staticmethod
    async def delete(session: AsyncSession, cat: CategoriaFinanceira) -> None:
        await session.delete(cat)
        await session.flush()


class ContaService:
    @staticmethod
    async def list(session: AsyncSession, apenas_ativos: bool = True) -> Sequence[ContaCaixa]:
        stmt = select(ContaCaixa).order_by(ContaCaixa.nome)
        if apenas_ativos:
            stmt = stmt.where(ContaCaixa.ativo.is_(True))
        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    async def get(session: AsyncSession, conta_id: int) -> ContaCaixa:
        conta = await session.get(ContaCaixa, conta_id)
        if conta is None:
            raise NoResultFound(f"Conta {conta_id} não encontrada")
        return conta

    @staticmethod
    async def create(session: AsyncSession, nome: str, ativo: bool = True) -> ContaCaixa:
        conta = ContaCaixa(nome=nome, ativo=ativo)
        session.add(conta)
        await session.flush()
        return conta

    @staticmethod
    async def update(
        session: AsyncSession,
        conta: ContaCaixa,
        payload: dict,
    ) -> ContaCaixa:
        for k, v in payload.items():
            if v is not None:
                setattr(conta, k, v)
        await session.flush()
        return conta

    @staticmethod
    async def delete(session: AsyncSession, conta: ContaCaixa) -> None:
        await session.delete(conta)
        await session.flush()


class LancamentoService:
    """Operações de LancamentoFinanceiro escopadas por evento."""

    @staticmethod
    async def list(
        session: AsyncSession,
        evento_id: int,
        *,
        tipo: str | None = None,
        categoria_id: int | None = None,
        conta_id: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[LancamentoFinanceiro], int]:
        """Retorna (items, total) paginado."""
        filters = [LancamentoFinanceiro.evento_id == evento_id]
        if tipo:
            filters.append(LancamentoFinanceiro.tipo == tipo)
        if categoria_id:
            filters.append(LancamentoFinanceiro.categoria_id == categoria_id)
        if conta_id:
            filters.append(LancamentoFinanceiro.conta_id == conta_id)
        if data_inicio:
            filters.append(LancamentoFinanceiro.data >= data_inicio)
        if data_fim:
            filters.append(LancamentoFinanceiro.data <= data_fim)

        count_stmt = select(func.count()).select_from(LancamentoFinanceiro).where(*filters)
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            select(LancamentoFinanceiro)
            .where(*filters)
            .order_by(LancamentoFinanceiro.data.desc(), LancamentoFinanceiro.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    @staticmethod
    async def get(session: AsyncSession, lancamento_id: int) -> LancamentoFinanceiro:
        lanc = await session.get(LancamentoFinanceiro, lancamento_id)
        if lanc is None:
            raise NoResultFound(f"Lançamento {lancamento_id} não encontrado")
        return lanc

    @staticmethod
    async def create(
        session: AsyncSession,
        evento_id: int,
        payload: LancamentoCreate,
        user_id: int,
    ) -> LancamentoFinanceiro:
        evento = await session.get(Evento, evento_id)
        if evento is None:
            raise ValueError("Evento não encontrado")
        if evento.fechado or evento.status == Evento.ENCERRADO:
            raise ValueError("Evento encerrado - lançamentos bloqueados")

        # validação cruzada: categoria.tipo == tipo
        cat = await session.get(CategoriaFinanceira, payload.categoria_id)
        if cat is None:
            raise ValueError("Categoria não encontrada")
        if cat.tipo != payload.tipo:
            raise ValueError(f"Categoria '{cat.nome}' é do tipo {cat.tipo}, incompatível com {payload.tipo}")
        if await session.get(ContaCaixa, payload.conta_id) is None:
            raise ValueError("Conta de caixa não encontrada")

        lanc = LancamentoFinanceiro(
            evento_id=evento_id,
            criado_por_id=user_id,
            **payload.model_dump(),
        )
        lanc.anexos = []
        session.add(lanc)
        await session.flush()
        return lanc

    @staticmethod
    async def update(
        session: AsyncSession,
        lancamento: LancamentoFinanceiro,
        payload: LancamentoUpdate,
        user_id: int,
    ) -> LancamentoFinanceiro:
        evento = await session.get(Evento, lancamento.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - lançamentos bloqueados")

        data = payload.model_dump(exclude_unset=True)
        if "categoria_id" in data and data["categoria_id"] is not None:
            cat = await session.get(CategoriaFinanceira, data["categoria_id"])
            if cat is None:
                raise ValueError("Categoria não encontrada")
            novo_tipo = data.get("tipo", lancamento.tipo)
            if cat.tipo != novo_tipo:
                raise ValueError(
                    f"Categoria '{cat.nome}' é do tipo {cat.tipo}, incompatível com {novo_tipo}"
                )
        for key, value in data.items():
            setattr(lancamento, key, value)
        lancamento.atualizado_por_id = user_id
        lancamento.atualizado_em = datetime.utcnow()
        await session.flush()
        return lancamento

    @staticmethod
    async def delete(session: AsyncSession, lancamento: LancamentoFinanceiro) -> None:
        evento = await session.get(Evento, lancamento.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - lançamentos bloqueados")

        await session.delete(lancamento)
        await session.flush()

    @staticmethod
    async def dashboard(
        session: AsyncSession,
        evento_id: int,
    ) -> dict[str, object]:
        """KPIs agregados por evento - equivalente a apps/finance/views/dashboard.py."""
        stmt = select(LancamentoFinanceiro).where(LancamentoFinanceiro.evento_id == evento_id)
        lancs = (await session.execute(stmt)).scalars().all()

        receitas = sum((l.valor for l in lancs if l.tipo == LancamentoFinanceiro.RECEITA), Decimal("0"))
        despesas = sum((l.valor for l in lancs if l.tipo == LancamentoFinanceiro.DESPESA), Decimal("0"))

        por_forma: dict[str, Decimal] = {}
        por_cat: dict[str, Decimal] = {}
        for l in lancs:
            por_forma[l.forma_pagamento] = por_forma.get(l.forma_pagamento, Decimal("0")) + l.valor
            if l.categoria is not None:
                nome = l.categoria.nome
                por_cat[nome] = por_cat.get(nome, Decimal("0")) + l.valor

        return {
            "receitas": receitas,
            "despesas": despesas,
            "saldo": receitas - despesas,
            "total_lancamentos": len(lancs),
            "por_forma_pagamento": por_forma,
            "por_categoria": por_cat,
        }


class ReportService:
    """Relatórios financeiros — DRE, fluxo de caixa, conciliação, relatório oficial."""

    @staticmethod
    def _build_base_stmt(evento_id: int, *, data_inicio: date | None = None, data_fim: date | None = None):
        stmt = select(LancamentoFinanceiro).where(LancamentoFinanceiro.evento_id == evento_id)
        if data_inicio:
            stmt = stmt.where(LancamentoFinanceiro.data >= data_inicio)
        if data_fim:
            stmt = stmt.where(LancamentoFinanceiro.data <= data_fim)
        return stmt

    @staticmethod
    async def dre(
        session: AsyncSession,
        evento_id: int,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> dict[str, object]:
        """DRE — agrega receitas/despesas por categoria, com total e margem."""
        # Totais
        rec_agg = await session.execute(
            select(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0))
            .where(LancamentoFinanceiro.evento_id == evento_id, LancamentoFinanceiro.tipo == LancamentoFinanceiro.RECEITA)
        )
        total_receitas = rec_agg.scalar_one()

        desp_agg = await session.execute(
            select(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0))
            .where(LancamentoFinanceiro.evento_id == evento_id, LancamentoFinanceiro.tipo == LancamentoFinanceiro.DESPESA)
        )
        total_despesas = desp_agg.scalar_one()

        resultado = total_receitas - total_despesas
        margem = (float(resultado) / float(total_receitas)) * 100 if total_receitas else None

        # Agrupa receitas/despesas por categoria via join
        rows = await session.execute(
            select(
                LancamentoFinanceiro.tipo,
                func.coalesce(CategoriaFinanceira.nome, "Sem categoria").label("cat_nome"),
                func.sum(LancamentoFinanceiro.valor).label("total"),
            )
            .join(CategoriaFinanceira, LancamentoFinanceiro.categoria_id == CategoriaFinanceira.id)
            .where(LancamentoFinanceiro.evento_id == evento_id)
            .group_by(LancamentoFinanceiro.tipo, CategoriaFinanceira.nome)
            .order_by(func.sum(LancamentoFinanceiro.valor).desc())
        )
        receitas_cat, despesas_cat = [], []
        for row in rows:
            item = {"categoria": row.cat_nome, "total": row.total}
            if row.tipo == LancamentoFinanceiro.RECEITA:
                receitas_cat.append(item)
            else:
                despesas_cat.append(item)

        return {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
            "resultado_liquido": resultado,
            "margem_percentual": margem,
            "receitas_por_categoria": receitas_cat,
            "despesas_por_categoria": despesas_cat,
        }

    @staticmethod
    async def cash_flow(
        session: AsyncSession,
        evento_id: int,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> dict[str, object]:
        """Fluxo de caixa diário com saldo acumulado."""
        base = ReportService._build_base_stmt(evento_id, data_inicio=data_inicio, data_fim=data_fim)

        rows = await session.execute(
            select(
                LancamentoFinanceiro.data,
                func.coalesce(
                    func.sum(case((LancamentoFinanceiro.tipo == LancamentoFinanceiro.RECEITA, LancamentoFinanceiro.valor), else_=0)),
                    0,
                ).label("receitas"),
                func.coalesce(
                    func.sum(case((LancamentoFinanceiro.tipo == LancamentoFinanceiro.DESPESA, LancamentoFinanceiro.valor), else_=0)),
                    0,
                ).label("despesas"),
            )
            .where(LancamentoFinanceiro.evento_id == evento_id)
            .group_by(LancamentoFinanceiro.data)
            .order_by(LancamentoFinanceiro.data)
        )

        linhas = []
        saldo_acum = Decimal("0")
        for row in rows:
            saldo_dia = row.receitas - row.despesas
            saldo_acum += saldo_dia
            linhas.append({
                "data": row.data,
                "receitas": row.receitas,
                "despesas": row.despesas,
                "saldo_dia": saldo_dia,
                "saldo_acumulado": saldo_acum,
            })

        total_rec = sum(l["receitas"] for l in linhas)
        total_desp = sum(l["despesas"] for l in linhas)

        return {
            "linhas": linhas,
            "total_receitas": total_rec,
            "total_despesas": total_desp,
            "saldo_final": saldo_acum,
        }

    @staticmethod
    async def reconciliation(
        session: AsyncSession,
        evento_id: int,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> dict[str, object]:
        """Conciliação por forma de pagamento."""
        rows = await session.execute(
            select(
                LancamentoFinanceiro.forma_pagamento,
                LancamentoFinanceiro.tipo,
                func.sum(LancamentoFinanceiro.valor).label("total"),
            )
            .where(LancamentoFinanceiro.evento_id == evento_id)
            .group_by(LancamentoFinanceiro.forma_pagamento, LancamentoFinanceiro.tipo)
        )

        aggr: dict[str, dict[str, Decimal]] = {}
        for row in rows:
            entry = aggr.setdefault(row.forma_pagamento, {"receitas": Decimal("0"), "despesas": Decimal("0")})
            if row.tipo == LancamentoFinanceiro.RECEITA:
                entry["receitas"] += row.total
            else:
                entry["despesas"] += row.total

        linhas = []
        total_rec = Decimal("0")
        total_desp = Decimal("0")
        for forma in sorted(aggr):
            rec = aggr[forma]["receitas"]
            desp = aggr[forma]["despesas"]
            total_rec += rec
            total_desp += desp
            linhas.append({
                "forma_pagamento": forma,
                "receitas": rec,
                "despesas": desp,
                "total": rec - desp,
            })

        return {
            "linhas": linhas,
            "total_receitas": total_rec,
            "total_despesas": total_desp,
            "saldo": total_rec - total_desp,
        }

    @staticmethod
    async def official_report(
        session: AsyncSession,
        evento_id: int,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> dict[str, object]:
        """Relatório oficial — listagem completa com totais, para impressão."""
        base = ReportService._build_base_stmt(evento_id, data_inicio=data_inicio, data_fim=data_fim)

        receitas_rows = await session.execute(
            base.where(LancamentoFinanceiro.tipo == LancamentoFinanceiro.RECEITA)
            .order_by(LancamentoFinanceiro.data, LancamentoFinanceiro.id)
        )
        despesas_rows = await session.execute(
            base.where(LancamentoFinanceiro.tipo == LancamentoFinanceiro.DESPESA)
            .order_by(LancamentoFinanceiro.data, LancamentoFinanceiro.id)
        )

        receitas = receitas_rows.scalars().all()
        despesas = despesas_rows.scalars().all()

        total_rec = sum((l.valor for l in receitas), Decimal("0"))
        total_desp = sum((l.valor for l in despesas), Decimal("0"))

        return {
            "receitas": [{"id": l.id, "data": l.data, "descricao": l.descricao, "categoria": l.categoria.nome if l.categoria else "", "valor": l.valor, "forma_pagamento": l.forma_pagamento} for l in receitas],
            "despesas": [{"id": l.id, "data": l.data, "descricao": l.descricao, "categoria": l.categoria.nome if l.categoria else "", "valor": l.valor, "forma_pagamento": l.forma_pagamento} for l in despesas],
            "total_receitas": total_rec,
            "total_despesas": total_desp,
            "saldo": total_rec - total_desp,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }