"""Testes unitários do módulo de Eventos (core) e integrações de encerramento."""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Evento, ConfiguracaoEvento
from app.core.schemas import EventoCreate, EventoUpdate
from app.core.services import EventoService

from app.finance.services import LancamentoService
from app.finance.schemas import LancamentoCreate
from app.lodging.services import ReservaChaleService, AcaoChaleService
from app.lodging.schemas import ReservaCreate, AcaoCreate


@pytest.mark.asyncio
async def test_list_ativos() -> None:
    session = AsyncMock(spec=AsyncSession)
    mock_events = [
        Evento(id=1, nome="Evento Ativo 1", ativo=True),
        Evento(id=2, nome="Evento Ativo 2", ativo=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_events
    session.execute.return_value = mock_result

    result = await EventoService.list_ativos(session)

    assert len(result) == 2
    assert result[0].nome == "Evento Ativo 1"
    assert result[1].nome == "Evento Ativo 2"
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_evento_sucesso() -> None:
    session = AsyncMock(spec=AsyncSession)
    mock_evento = Evento(id=42, nome="Seminário X", ativo=True)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_evento
    session.execute.return_value = mock_result

    result = await EventoService.get(session, 42)

    assert result.id == 42
    assert result.nome == "Seminário X"
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_evento_nao_encontrado() -> None:
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    with pytest.raises(NoResultFound) as exc_info:
        await EventoService.get(session, 999)
    assert "Evento 999 não encontrado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_evento() -> None:
    session = AsyncMock(spec=AsyncSession)
    payload = EventoCreate(
        nome="Novo Retiro",
        data_inicio="2026-07-20T08:00:00Z",
        data_fim="2026-07-22T18:00:00Z",
        status="PLANEJADO",
        ativo=True,
        fechado=False,
        taxa_base=Decimal("60.00"),
        taxa_trabalhador=Decimal("30.00"),
        adicional_chale=Decimal("120.00"),
        prev_participantes=100,
        prev_trabalhadores=50,
        observacoes="Nenhuma",
        centro_custo_id=1,
        responsavel_geral_id=2,
    )

    evento = await EventoService.create(session, payload)

    assert evento.nome == "Novo Retiro"
    assert session.add.call_count == 2
    assert session.flush.call_count == 2


@pytest.mark.asyncio
async def test_update_evento() -> None:
    session = AsyncMock(spec=AsyncSession)
    evento = Evento(id=1, nome="Nome Antigo", taxa_base=Decimal("50.00"))
    payload = EventoUpdate(nome="Nome Novo", taxa_base=Decimal("55.00"))

    updated = await EventoService.update(session, evento, payload)

    assert updated.nome == "Nome Novo"
    assert updated.taxa_base == Decimal("55.00")
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_encerrar_evento() -> None:
    session = AsyncMock(spec=AsyncSession)
    evento = Evento(id=5, nome="Retiro a ser Encerrado", status="EM_ANDAMENTO", fechado=False)

    mock_config = ConfiguracaoEvento(evento_id=5, permite_vendas_pos=True)
    mock_config_result = MagicMock()
    mock_config_result.scalar_one_or_none.return_value = mock_config

    mock_local_result = MagicMock()
    mock_local_result.all.return_value = [(10,)]

    mock_pl = MagicMock()
    mock_pl.produto = MagicMock()
    mock_pl.produto.perene = False
    mock_pl.estoque_atual = Decimal("15.00")

    mock_pl_result = MagicMock()
    mock_pl_result.scalars.return_value.all.return_value = [mock_pl]

    session.execute.side_effect = [
        mock_config_result,
        mock_local_result,
        mock_pl_result,
    ]

    encerrado = await EventoService.encerrar(session, evento, user_id=9)

    assert encerrado.status == Evento.ENCERRADO
    assert encerrado.fechado is True
    assert mock_config.data_fechamento is not None
    assert mock_pl.estoque_atual == Decimal("0.00")
    assert session.flush.call_count == 1


@pytest.mark.asyncio
async def test_finance_bloqueia_lancamento_evento_encerrado() -> None:
    session = AsyncMock(spec=AsyncSession)
    evento = Evento(id=1, nome="Retiro Encerrado", status="ENCERRADO", fechado=True)
    session.get.return_value = evento

    payload = LancamentoCreate(
        tipo="RECEITA",
        categoria_id=1,
        conta_id=1,
        data="2026-07-16",
        descricao="Teste fechamento",
        valor=Decimal("10.00"),
        forma_pagamento="DINHEIRO",
    )

    with pytest.raises(ValueError) as exc:
        await LancamentoService.create(session, 1, payload, user_id=9)
    assert "Evento encerrado - lançamentos bloqueados" in str(exc.value)


@pytest.mark.asyncio
async def test_lodging_bloqueia_reserva_evento_encerrado() -> None:
    session = MagicMock(spec=AsyncSession)
    evento = Evento(id=2, nome="Retiro Encerrado", status="ENCERRADO", fechado=True)
    
    async def mock_get(model, ident, **kwargs):
        if model == Evento:
            return evento
        return None
    session.get = mock_get

    payload = ReservaCreate(
        chale_id=1,
        responsavel_nome="Fulano",
        data_entrada="2026-07-20",
        data_saida="2026-07-22",
        qtd_pessoas=2,
        qtd_criancas=0,
        possui_necessidade_especial=False,
        detalhes_necessidade_especial="",
        valor_adicional=Decimal("0.00"),
        pago=False,
    )

    with pytest.raises(ValueError) as exc:
        await ReservaChaleService.create(session, 2, payload, user_id=9)
    assert "Evento encerrado - reservas bloqueadas" in str(exc.value)


@pytest.mark.asyncio
async def test_lodging_bloqueia_acao_evento_encerrado() -> None:
    session = MagicMock(spec=AsyncSession)
    evento = Evento(id=3, nome="Retiro Encerrado", status="ENCERRADO", fechado=True)
    
    async def mock_get(model, ident, **kwargs):
        if model == Evento:
            return evento
        return None
    session.get = mock_get

    payload = AcaoCreate(
        chale_id=1,
        tipo="MANUTENCAO",
        titulo="Pintura",
        descricao="Manutenção geral",
        data_inicio="2026-07-20",
        data_fim="2026-07-22",
    )

    with pytest.raises(ValueError) as exc:
        await AcaoChaleService.create(session, 3, payload, user_id=9)
    assert "Evento encerrado - ações bloqueadas" in str(exc.value)
