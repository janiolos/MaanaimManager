"""Serviços do módulo lodging.

Inclui as 7 regras de validação de ReservaChale (transplantadas de `clean()` do Django
para `ReservaChaleService.validar_periodo`) e as 3 regras de AcaoChale.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.models import LancamentoFinanceiro
from app.lodging.models import AcaoChale, Chale, ReservaChale
from app.lodging.schemas import AcaoCreate, AcaoUpdate, ChaleCreate, ChaleUpdate, ReservaCreate, ReservaUpdate
from app.core.models import Evento


# ============================ Chale ============================


class ChaleService:
    @staticmethod
    async def list(session: AsyncSession, status: str | None = None) -> Sequence[Chale]:
        stmt = select(Chale).order_by(Chale.codigo)
        if status:
            stmt = stmt.where(Chale.status == status)
        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    async def get(session: AsyncSession, chale_id: int) -> Chale:
        c = await session.get(Chale, chale_id)
        if c is None:
            raise NoResultFound(f"Chalé {chale_id} não encontrado")
        return c

    @staticmethod
    async def create(session: AsyncSession, payload: ChaleCreate) -> Chale:
        c = Chale(**payload.model_dump())
        session.add(c)
        await session.flush()
        return c

    @staticmethod
    async def update(session: AsyncSession, chale: Chale, payload: ChaleUpdate) -> Chale:
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(chale, k, v)
        await session.flush()
        return chale

    @staticmethod
    async def delete(session: AsyncSession, chale: Chale) -> None:
        await session.delete(chale)
        await session.flush()


# ============================ Reserva ============================


class ReservaChaleService:
    @staticmethod
    async def _validate_periodo(
        session: AsyncSession,
        *,
        chale_id: int,
        evento_id: int,
        data_entrada: date,
        data_saida: date,
        total_hospedes: int,
        possui_necessidade_especial: bool,
        detalhes_necessidade_especial: str,
        exclude_reserva_id: int | None = None,
    ) -> None:
        """7 regras de validação - replica o `ReservaChale.clean()` do Django."""
        # 1. período obrigatório
        if not data_entrada or not data_saida:
            raise ValueError("Informe o período da reserva (data_entrada + data_saida)")

        # 2. data_saida > data_entrada
        if data_saida <= data_entrada:
            raise ValueError("A data de saída deve ser maior que a de entrada")

        # 3. detalhes de necessidade especial obrigatórios
        if possui_necessidade_especial and not detalhes_necessidade_especial.strip():
            raise ValueError(
                "Detalhe as necessidades especiais para suporte da equipe"
            )

        chale = await session.get(Chale, chale_id)
        if chale is None:
            raise ValueError("Chalé não encontrado")

        # 4. capacidade
        if total_hospedes > chale.capacidade:
            raise ValueError(
                f"Total de hóspedes ({total_hospedes}) excede a capacidade do chalé ({chale.capacidade})"
            )

        # 5. status do chalé
        if chale.status != Chale.ATIVO:
            raise ValueError("Chalé indisponível para reserva")

        # 6. conflito com outra ReservaChale ativa (overlap half-open)
        conflito_stmt = (
            select(ReservaChale)
            .where(
                ReservaChale.evento_id == evento_id,
                ReservaChale.chale_id == chale_id,
                ReservaChale.status.in_(ReservaChale.STATUS_ATIVOS),
                ReservaChale.data_entrada < data_saida,
                ReservaChale.data_saida > data_entrada,
            )
        )
        if exclude_reserva_id is not None:
            conflito_stmt = conflito_stmt.where(ReservaChale.id != exclude_reserva_id)
        conflito = (await session.execute(conflito_stmt)).scalars().first()
        if conflito is not None:
            raise ValueError(
                f"Chalé já reservado para este período (reserva #{conflito.id}, "
                f"{conflito.data_entrada} → {conflito.data_saida})"
            )

        # 7. conflito com AcaoChale ativa (bloqueio/manutenção)
        acao_stmt = (
            select(AcaoChale)
            .where(
                AcaoChale.evento_id == evento_id,
                AcaoChale.chale_id == chale_id,
                AcaoChale.ativo.is_(True),
                AcaoChale.data_inicio < data_saida,
                AcaoChale.data_fim > data_entrada,
            )
        )
        acao = (await session.execute(acao_stmt)).scalars().first()
        if acao is not None:
            raise ValueError(
                f"Existe {acao.tipo.lower()} no período ({acao.data_inicio} → {acao.data_fim})"
            )

    @staticmethod
    async def list(
        session: AsyncSession,
        evento_id: int,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[Sequence[ReservaChale], int]:
        filters = [ReservaChale.evento_id == evento_id]
        if status:
            filters.append(ReservaChale.status == status)
        total = (
            await session.execute(
                select(func.count()).select_from(ReservaChale).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(ReservaChale)
            .where(*filters)
            .order_by(ReservaChale.criado_em.desc(), ReservaChale.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await session.execute(stmt)).scalars().all(), total

    @staticmethod
    async def get(session: AsyncSession, reserva_id: int) -> ReservaChale:
        r = await session.get(ReservaChale, reserva_id)
        if r is None:
            raise NoResultFound(f"Reserva {reserva_id} não encontrada")
        return r

    @staticmethod
    async def create(
        session: AsyncSession,
        evento_id: int,
        payload: ReservaCreate,
        user_id: int,
    ) -> ReservaChale:
        evento = await session.get(Evento, evento_id)
        if evento is None:
            raise ValueError("Evento não encontrado")
        if evento.fechado or evento.status == Evento.ENCERRADO:
            raise ValueError("Evento encerrado - reservas bloqueadas")

        total_hospedes = payload.qtd_pessoas + payload.qtd_criancas
        await ReservaChaleService._validate_periodo(
            session,
            chale_id=payload.chale_id,
            evento_id=evento_id,
            data_entrada=payload.data_entrada,
            data_saida=payload.data_saida,
            total_hospedes=total_hospedes,
            possui_necessidade_especial=payload.possui_necessidade_especial,
            detalhes_necessidade_especial=payload.detalhes_necessidade_especial,
        )

        reserva = ReservaChale(
            evento_id=evento_id,
            criado_por_id=user_id,
            **payload.model_dump(),
        )
        session.add(reserva)
        await session.flush()

        # Se pago + forma_pagamento + conta, cria LancamentoFinanceiro RECEITA
        if (
            reserva.pago
            and reserva.forma_pagamento
            and reserva.conta_id is not None
            and reserva.valor_adicional > 0
        ):
            await ReservaChaleService._gerar_lancamento(session, reserva, user_id)
        return reserva

    @staticmethod
    async def update(
        session: AsyncSession,
        reserva: ReservaChale,
        payload: ReservaUpdate,
        user_id: int,
    ) -> ReservaChale:
        evento = await session.get(Evento, reserva.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - reservas bloqueadas")

        if reserva.status == ReservaChale.CANCELADA:
            raise ValueError("Reserva cancelada não pode ser editada")

        data = payload.model_dump(exclude_unset=True)
        # valida novo período se algum campo crítico mudou
        campos_criticos = {"chale_id", "data_entrada", "data_saida", "qtd_pessoas", "qtd_criancas",
                          "possui_necessidade_especial", "detalhes_necessidade_especial"}
        if campos_criticos & data.keys():
            novo_chale_id = data.get("chale_id", reserva.chale_id)
            nova_entrada = data.get("data_entrada", reserva.data_entrada)
            nova_saida = data.get("data_saida", reserva.data_saida)
            nova_qtd = data.get("qtd_pessoas", reserva.qtd_pessoas)
            nova_qtd_criancas = data.get("qtd_criancas", reserva.qtd_criancas)
            nova_necessidade = data.get("possui_necessidade_especial", reserva.possui_necessidade_especial)
            novos_detalhes = data.get("detalhes_necessidade_especial", reserva.detalhes_necessidade_especial)
            if nova_entrada is not None and nova_saida is not None:
                await ReservaChaleService._validate_periodo(
                    session,
                    chale_id=novo_chale_id,
                    evento_id=reserva.evento_id,
                    data_entrada=nova_entrada,
                    data_saida=nova_saida,
                    total_hospedes=nova_qtd + nova_qtd_criancas,
                    possui_necessidade_especial=nova_necessidade,
                    detalhes_necessidade_especial=novos_detalhes,
                    exclude_reserva_id=reserva.id,
                )

        for k, v in data.items():
            setattr(reserva, k, v)
        reserva.atualizado_por_id = user_id
        await session.flush()

        # se passou a pago e tem lancamento, criar
        if (
            reserva.pago
            and reserva.forma_pagamento
            and reserva.conta_id is not None
            and reserva.valor_adicional > 0
            and reserva.lancamento_financeiro_id is None
        ):
            await ReservaChaleService._gerar_lancamento(session, reserva, user_id)
        return reserva

    @staticmethod
    async def cancelar(session: AsyncSession, reserva: ReservaChale) -> ReservaChale:
        evento = await session.get(Evento, reserva.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - reservas bloqueadas")

        if reserva.status == ReservaChale.CANCELADA:
            raise ValueError("Reserva já está cancelada")
        reserva.status = ReservaChale.CANCELADA
        await session.flush()
        return reserva

    @staticmethod
    async def _gerar_lancamento(
        session: AsyncSession,
        reserva: ReservaChale,
        user_id: int,
    ) -> None:
        """Cria LancamentoFinanceiro RECEITA categoria 'Hospedagem' (cria se faltar)."""
        from app.finance.models import CategoriaFinanceira, ContaCaixa
        from sqlalchemy import select as _sel

        cat = (
            await session.execute(
                _sel(CategoriaFinanceira).where(
                    CategoriaFinanceira.nome == "Hospedagem",
                    CategoriaFinanceira.tipo == LancamentoFinanceiro.RECEITA,
                )
            )
        ).scalar_one_or_none()
        if cat is None:
            cat = CategoriaFinanceira(nome="Hospedagem", tipo=LancamentoFinanceiro.RECEITA)
            session.add(cat)
            await session.flush()

        if await session.get(ContaCaixa, reserva.conta_id) is None:
            raise ValueError("Conta de caixa não encontrada")

        lancamento = LancamentoFinanceiro(
            evento_id=reserva.evento_id,
            tipo=LancamentoFinanceiro.RECEITA,
            categoria_id=cat.id,
            conta_id=reserva.conta_id,
            data=reserva.data_entrada,
            descricao=f"Hospedagem {reserva.chale.codigo} - {reserva.responsavel_nome}",
            valor=reserva.valor_adicional,
            forma_pagamento=reserva.forma_pagamento,
            criado_por_id=user_id,
            setor_origem="lodging",
            pessoa=reserva.responsavel_nome,
        )
        session.add(lancamento)
        await session.flush()
        reserva.lancamento_financeiro_id = lancamento.id
        await session.flush()


# ============================ Acao ============================


class AcaoChaleService:
    @staticmethod
    async def _validate_periodo(
        session: AsyncSession,
        *,
        chale_id: int,
        evento_id: int,
        data_inicio: date,
        data_fim: date,
        exclude_acao_id: int | None = None,
    ) -> None:
        # 1. data_fim > data_inicio
        if data_fim <= data_inicio:
            raise ValueError("Data final deve ser maior que data inicial")

        # 2. sem ReservaChale ativa em sobreposição
        conflito_reserva = (
            await session.execute(
                select(ReservaChale).where(
                    ReservaChale.evento_id == evento_id,
                    ReservaChale.chale_id == chale_id,
                    ReservaChale.status.in_(ReservaChale.STATUS_ATIVOS),
                    ReservaChale.data_entrada < data_fim,
                    ReservaChale.data_saida > data_inicio,
                )
            )
        ).scalars().first()
        if conflito_reserva is not None:
            raise ValueError(
                f"Existe reserva ativa no período (reserva #{conflito_reserva.id})"
            )

        # 3. sem outra AcaoChale ativa sobreposta
        stmt_acao = (
            select(AcaoChale)
            .where(
                AcaoChale.evento_id == evento_id,
                AcaoChale.chale_id == chale_id,
                AcaoChale.ativo.is_(True),
                AcaoChale.data_inicio < data_fim,
                AcaoChale.data_fim > data_inicio,
            )
        )
        if exclude_acao_id is not None:
            stmt_acao = stmt_acao.where(AcaoChale.id != exclude_acao_id)
        conflito_acao = (await session.execute(stmt_acao)).scalars().first()
        if conflito_acao is not None:
            raise ValueError(
                f"Já existe bloqueio/manutenção no período (ação #{conflito_acao.id})"
            )

    @staticmethod
    async def list(
        session: AsyncSession,
        evento_id: int,
        *,
        ativo: bool | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[Sequence[AcaoChale], int]:
        filters = [AcaoChale.evento_id == evento_id]
        if ativo is not None:
            filters.append(AcaoChale.ativo.is_(ativo))
        total = (
            await session.execute(
                select(func.count()).select_from(AcaoChale).where(*filters)
            )
        ).scalar_one()
        stmt = (
            select(AcaoChale)
            .where(*filters)
            .order_by(AcaoChale.data_inicio.desc(), AcaoChale.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await session.execute(stmt)).scalars().all(), total

    @staticmethod
    async def get(session: AsyncSession, acao_id: int) -> AcaoChale:
        a = await session.get(AcaoChale, acao_id)
        if a is None:
            raise NoResultFound(f"Ação {acao_id} não encontrada")
        return a

    @staticmethod
    async def create(
        session: AsyncSession,
        evento_id: int,
        payload: AcaoCreate,
        user_id: int,
    ) -> AcaoChale:
        evento = await session.get(Evento, evento_id)
        if evento is None:
            raise ValueError("Evento não encontrado")
        if evento.fechado or evento.status == Evento.ENCERRADO:
            raise ValueError("Evento encerrado - ações bloqueadas")

        await AcaoChaleService._validate_periodo(
            session,
            chale_id=payload.chale_id,
            evento_id=evento_id,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
        )
        a = AcaoChale(evento_id=evento_id, criado_por_id=user_id, **payload.model_dump())
        session.add(a)
        await session.flush()
        return a

    @staticmethod
    async def update(
        session: AsyncSession,
        acao: AcaoChale,
        payload: AcaoUpdate,
        user_id: int,
    ) -> AcaoChale:
        evento = await session.get(Evento, acao.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - ações bloqueadas")

        data = payload.model_dump(exclude_unset=True)
        campos_criticos = {"chale_id", "data_inicio", "data_fim"}
        if campos_criticos & data.keys():
            novo_chale = data.get("chale_id", acao.chale_id)
            novo_ini = data.get("data_inicio", acao.data_inicio)
            novo_fim = data.get("data_fim", acao.data_fim)
            if novo_ini is not None and novo_fim is not None:
                await AcaoChaleService._validate_periodo(
                    session,
                    chale_id=novo_chale,
                    evento_id=acao.evento_id,
                    data_inicio=novo_ini,
                    data_fim=novo_fim,
                    exclude_acao_id=acao.id,
                )
        for k, v in data.items():
            setattr(acao, k, v)
        acao.atualizado_por_id = user_id
        await session.flush()
        return acao

    @staticmethod
    async def cancelar(session: AsyncSession, acao: AcaoChale) -> AcaoChale:
        evento = await session.get(Evento, acao.evento_id)
        if evento and (evento.fechado or evento.status == Evento.ENCERRADO):
            raise ValueError("Evento encerrado - ações bloqueadas")

        if not acao.ativo:
            raise ValueError("Ação já está inativa")
        acao.ativo = False
        await session.flush()
        return acao


# ============================ Dashboard + Mapa ============================


class LodgingDashboardService:
    @staticmethod
    async def dashboard(session: AsyncSession, evento_id: int) -> dict[str, object]:
        total_chales = (
            await session.execute(select(func.count()).select_from(Chale))
        ).scalar_one()
        chales_ativos = (
            await session.execute(
                select(func.count()).select_from(Chale).where(Chale.status == Chale.ATIVO)
            )
        ).scalar_one()
        chales_manut = (
            await session.execute(
                select(func.count()).select_from(Chale).where(Chale.status == Chale.MANUTENCAO)
            )
        ).scalar_one()
        reservas_ativas = (
            await session.execute(
                select(func.count())
                .select_from(ReservaChale)
                .where(
                    ReservaChale.evento_id == evento_id,
                    ReservaChale.status.in_(ReservaChale.STATUS_ATIVOS),
                )
            )
        ).scalar_one()
        reservas_conf = (
            await session.execute(
                select(func.count())
                .select_from(ReservaChale)
                .where(
                    ReservaChale.evento_id == evento_id,
                    ReservaChale.status == ReservaChale.CONFIRMADA,
                )
            )
        ).scalar_one()
        acoes_ativas = (
            await session.execute(
                select(func.count())
                .select_from(AcaoChale)
                .where(AcaoChale.evento_id == evento_id, AcaoChale.ativo.is_(True))
            )
        ).scalar_one()
        return {
            "total_chales": total_chales,
            "chales_ativos": chales_ativos,
            "chales_manutencao": chales_manut,
            "reservas_ativas": reservas_ativas,
            "reservas_confirmadas": reservas_conf,
            "acoes_ativas": acoes_ativas,
        }


class MapaService:
    """Mapa/timeline semanal: para cada chalé x dia, indica Reserva/Acao/Livre."""

    @staticmethod
    async def gerar(
        session: AsyncSession,
        evento_id: int,
        *,
        data_inicio: date | None = None,
        dias: int = 14,
    ) -> dict[str, object]:
        from app.lodging.models import Chale
        from app.lodging.schemas import ChaleOut
        from app.lodging.schemas import MapaCell

        chales = await ChaleService.list(session)
        # se data_inicio não informada, usa hoje
        inicio = data_inicio or date.today()
        lista_dias = [inicio + timedelta(days=i) for i in range(dias)]

        # busca reservas/acoes no período de uma vez
        fim = lista_dias[-1]
        reservas = (
            await session.execute(
                select(ReservaChale).where(
                    ReservaChale.evento_id == evento_id,
                    ReservaChale.status.in_(ReservaChale.STATUS_ATIVOS),
                    ReservaChale.data_entrada <= fim,
                    ReservaChale.data_saida >= inicio,
                )
            )
        ).scalars().all()

        acoes = (
            await session.execute(
                select(AcaoChale).where(
                    AcaoChale.evento_id == evento_id,
                    AcaoChale.ativo.is_(True),
                    AcaoChale.data_inicio <= fim,
                    AcaoChale.data_fim >= inicio,
                )
            )
        ).scalars().all()

        celulas: list[list[MapaCell]] = []
        for chale in chales:
            linha: list[MapaCell] = []
            for d in lista_dias:
                reserva = next(
                    (
                        r
                        for r in reservas
                        if r.chale_id == chale.id
                        and r.data_entrada is not None
                        and r.data_saida is not None
                        and r.data_entrada <= d < r.data_saida
                    ),
                    None,
                )
                if reserva is not None:
                    linha.append(
                        MapaCell(
                            chale_id=chale.id,
                            chale_codigo=chale.codigo,
                            data=d,
                            tipo="RESERVA",
                            label=reserva.responsavel_nome,
                            reserva_id=reserva.id,
                        )
                    )
                    continue
                acao = next(
                    (
                        a
                        for a in acoes
                        if a.chale_id == chale.id
                        and a.data_inicio <= d < a.data_fim
                    ),
                    None,
                )
                if acao is not None:
                    linha.append(
                        MapaCell(
                            chale_id=chale.id,
                            chale_codigo=chale.codigo,
                            data=d,
                            tipo="ACAO",
                            label=f"{acao.tipo}: {acao.titulo}",
                            acao_id=acao.id,
                        )
                    )
                    continue
                linha.append(
                    MapaCell(
                        chale_id=chale.id,
                        chale_codigo=chale.codigo,
                        data=d,
                        tipo="LIVRE",
                        label="",
                    )
                )
            celulas.append(linha)

        return {
            "chales": [ChaleOut.model_validate(c) for c in chales],
            "dias": lista_dias,
            "celulas": celulas,
        }