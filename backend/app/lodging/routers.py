"""Routers do módulo lodging - /api/v1/lodging/*."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, EventoAtualId, require_scopes
from app.db.session import get_session
from app.lodging import schemas, services
from app.lodging.schemas import (
    AcaoCreate,
    AcaoOut,
    AcaoUpdate,
    ChaleCreate,
    ChaleOut,
    ChaleUpdate,
    LodgingDashboard,
    ReservaCreate,
    ReservaOut,
    ReservaUpdate,
)

router = APIRouter(prefix="/lodging", tags=["lodging"])


def _require_evento(evento_id: int | None) -> int:
    if evento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum evento selecionado (header X-Evento-Id ausente)",
        )
    return evento_id


# ============================ Dashboard ============================


@router.get("/dashboard", response_model=LodgingDashboard)
async def dashboard(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> LodgingDashboard:
    ev_id = _require_evento(evento_id)
    data = await services.LodgingDashboardService.dashboard(session, ev_id)
    return LodgingDashboard(**data)


# ============================ Chales ============================


@router.get("/chales", response_model=list[ChaleOut])
async def chales_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(None),
) -> list[ChaleOut]:
    items = await services.ChaleService.list(session, status=status)
    return [ChaleOut.model_validate(c) for c in items]


@router.post("/chales", response_model=ChaleOut, status_code=201)
async def chale_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    payload: ChaleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChaleOut:
    try:
        c = await services.ChaleService.create(session, payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChaleOut.model_validate(c)


@router.get("/chales/{chale_id}", response_model=ChaleOut)
async def chale_detalhe(
    current: CurrentUser,
    chale_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChaleOut:
    try:
        c = await services.ChaleService.get(session, chale_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Chalé não encontrado") from exc
    return ChaleOut.model_validate(c)


@router.patch("/chales/{chale_id}", response_model=ChaleOut)
async def chale_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    chale_id: int,
    payload: ChaleUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChaleOut:
    try:
        c = await services.ChaleService.get(session, chale_id)
        c = await services.ChaleService.update(session, c, payload)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Chalé não encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChaleOut.model_validate(c)


@router.delete("/chales/{chale_id}", status_code=204)
async def chale_excluir(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    chale_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        c = await services.ChaleService.get(session, chale_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Chalé não encontrado") from exc
    await services.ChaleService.delete(session, c)


# ============================ Reservas ============================


@router.get("/reservas", response_model=dict)
async def reservas_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> dict:
    ev_id = _require_evento(evento_id)
    items, total = await services.ReservaChaleService.list(
        session, ev_id, status=status, page=page, page_size=page_size
    )
    return {
        "items": [ReservaOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/reservas", response_model=ReservaOut, status_code=201)
async def reserva_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    payload: ReservaCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> ReservaOut:
    ev_id = _require_evento(evento_id)
    try:
        r = await services.ReservaChaleService.create(session, ev_id, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReservaOut.model_validate(r)


@router.get("/reservas/{reserva_id}", response_model=ReservaOut)
async def reserva_detalhe(
    current: CurrentUser,
    reserva_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReservaOut:
    try:
        r = await services.ReservaChaleService.get(session, reserva_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Reserva não encontrada") from exc
    return ReservaOut.model_validate(r)


@router.patch("/reservas/{reserva_id}", response_model=ReservaOut)
async def reserva_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    reserva_id: int,
    payload: ReservaUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReservaOut:
    try:
        r = await services.ReservaChaleService.get(session, reserva_id)
        r = await services.ReservaChaleService.update(session, r, payload, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Reserva não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReservaOut.model_validate(r)


@router.post("/reservas/{reserva_id}/cancelar", response_model=ReservaOut)
async def reserva_cancelar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    reserva_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReservaOut:
    try:
        r = await services.ReservaChaleService.get(session, reserva_id)
        r = await services.ReservaChaleService.cancelar(session, r)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Reserva não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReservaOut.model_validate(r)


# ============================ Acoes ============================


@router.get("/acoes", response_model=dict)
async def acoes_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    ativo: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> dict:
    ev_id = _require_evento(evento_id)
    items, total = await services.AcaoChaleService.list(
        session, ev_id, ativo=ativo, page=page, page_size=page_size
    )
    return {
        "items": [AcaoOut.model_validate(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/acoes", response_model=AcaoOut, status_code=201)
async def acao_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    payload: AcaoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> AcaoOut:
    ev_id = _require_evento(evento_id)
    try:
        a = await services.AcaoChaleService.create(session, ev_id, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AcaoOut.model_validate(a)


@router.get("/acoes/{acao_id}", response_model=AcaoOut)
async def acao_detalhe(
    current: CurrentUser,
    acao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AcaoOut:
    try:
        a = await services.AcaoChaleService.get(session, acao_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Ação não encontrada") from exc
    return AcaoOut.model_validate(a)


@router.patch("/acoes/{acao_id}", response_model=AcaoOut)
async def acao_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    acao_id: int,
    payload: AcaoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AcaoOut:
    try:
        a = await services.AcaoChaleService.get(session, acao_id)
        a = await services.AcaoChaleService.update(session, a, payload, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Ação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AcaoOut.model_validate(a)


@router.post("/acoes/{acao_id}/cancelar", response_model=AcaoOut)
async def acao_cancelar(
    current: Annotated[CurrentUser, Depends(require_scopes("lodging:write"))],
    acao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AcaoOut:
    try:
        a = await services.AcaoChaleService.get(session, acao_id)
        a = await services.AcaoChaleService.cancelar(session, a)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Ação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AcaoOut.model_validate(a)


# ============================ Mapa ============================


@router.get("/mapa", response_model=schemas.MapaResponse)
async def mapa(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: date | None = Query(None),
    dias: int = Query(14, ge=1, le=60),
) -> schemas.MapaResponse:
    ev_id = _require_evento(evento_id)
    data = await services.MapaService.gerar(
        session, ev_id, data_inicio=data_inicio, dias=dias
    )
    return schemas.MapaResponse(**data)