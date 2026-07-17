"""Routers do módulo inventory - /api/v1/inventory/*."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, EventoAtualId, require_scopes
from app.db.session import get_session
from app.inventory import schemas, services
from app.inventory.schemas import (
    CotacaoAprovarIn,
    CotacaoCreate,
    CotacaoOut,
    CotacaoUpdate,
    EntradaEstoqueCreate,
    EntradaEstoqueOut,
    FornecedorCreate,
    FornecedorOut,
    FornecedorUpdate,
    InventoryDashboard,
    OrdemCompraOut,
    PaginatedOrdensCompra,
    PaginatedProdutos,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
    RequisicaoCreate,
    RequisicaoOut,
    RequisicaoUpdate,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _require_evento(evento_id: int | None) -> int:
    if evento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum evento selecionado (header X-Evento-Id ausente)",
        )
    return evento_id


# ============================ Dashboard ============================


@router.get("/dashboard", response_model=InventoryDashboard)
async def dashboard(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> InventoryDashboard:
    ev_id = _require_evento(evento_id)
    data = await services.InventoryDashboardService.dashboard(session, ev_id)
    return InventoryDashboard(**data)


# ============================ Produtos ============================


@router.get("/produtos", response_model=PaginatedProdutos)
async def produtos_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    ativo: bool | None = Query(None),
    busca: str | None = Query(None),
    categoria: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedProdutos:
    items, total = await services.ProdutoService.list(
        session,
        ativo=ativo,
        busca=busca,
        categoria=categoria,
        status=status,
        page=page,
        page_size=page_size,
    )
    return PaginatedProdutos(
        items=[ProdutoOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/produtos", response_model=ProdutoOut, status_code=201)
async def produto_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    payload: ProdutoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProdutoOut:
    try:
        p = await services.ProdutoService.create(session, payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ProdutoOut.model_validate(p)


@router.get("/produtos/{produto_id}", response_model=ProdutoOut)
async def produto_detalhe(
    current: CurrentUser,
    produto_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProdutoOut:
    try:
        p = await services.ProdutoService.get(session, produto_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Produto não encontrado") from exc
    return ProdutoOut.model_validate(p)


@router.patch("/produtos/{produto_id}", response_model=ProdutoOut)
async def produto_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    produto_id: int,
    payload: ProdutoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProdutoOut:
    try:
        p = await services.ProdutoService.get(session, produto_id)
        p = await services.ProdutoService.update(session, p, payload)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Produto não encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ProdutoOut.model_validate(p)


@router.delete("/produtos/{produto_id}", status_code=204)
async def produto_excluir(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    produto_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        p = await services.ProdutoService.get(session, produto_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Produto não encontrado") from exc
    await services.ProdutoService.delete(session, p)


# ============================ Entrada Estoque ============================


@router.post("/entradas", response_model=EntradaEstoqueOut, status_code=201)
async def entrada_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    payload: EntradaEstoqueCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EntradaEstoqueOut:
    try:
        _, entrada = await services.ProdutoService.registrar_entrada(
            session, payload, current.id
        )
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EntradaEstoqueOut.model_validate(entrada)


# ============================ Requisições ============================


@router.get("/requisicoes", response_model=dict)
async def requisicoes_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> dict:
    ev_id = _require_evento(evento_id)
    items, total = await services.RequisicaoService.list(
        session, ev_id, status=status, page=page, page_size=page_size
    )
    return {
        "items": [RequisicaoOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/requisicoes", response_model=RequisicaoOut, status_code=201)
async def requisicao_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    payload: RequisicaoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> RequisicaoOut:
    ev_id = _require_evento(evento_id)
    try:
        r = await services.RequisicaoService.create(session, ev_id, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RequisicaoOut.model_validate(r)


@router.get("/requisicoes/{requisicao_id}", response_model=RequisicaoOut)
async def requisicao_detalhe(
    current: CurrentUser,
    requisicao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequisicaoOut:
    try:
        r = await services.RequisicaoService.get(session, requisicao_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Requisição não encontrada") from exc
    return RequisicaoOut.model_validate(r)


@router.patch("/requisicoes/{requisicao_id}", response_model=RequisicaoOut)
async def requisicao_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    requisicao_id: int,
    payload: RequisicaoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequisicaoOut:
    try:
        r = await services.RequisicaoService.get(session, requisicao_id)
        r = await services.RequisicaoService.update(session, r, payload)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Requisição não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RequisicaoOut.model_validate(r)


@router.post("/requisicoes/{requisicao_id}/finalizar", response_model=RequisicaoOut)
async def requisicao_finalizar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    requisicao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequisicaoOut:
    try:
        r = await services.RequisicaoService.get(session, requisicao_id)
        r = await services.RequisicaoService.finalizar(session, r, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Requisição não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RequisicaoOut.model_validate(r)


@router.post("/requisicoes/{requisicao_id}/cancelar", response_model=RequisicaoOut)
async def requisicao_cancelar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    requisicao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequisicaoOut:
    try:
        r = await services.RequisicaoService.get(session, requisicao_id)
        r = await services.RequisicaoService.cancelar(session, r)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Requisição não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RequisicaoOut.model_validate(r)


# ============================ Fornecedores ============================


@router.get("/fornecedores", response_model=list[FornecedorOut])
async def fornecedores_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    ativo: bool | None = Query(None),
) -> list[FornecedorOut]:
    items = await services.FornecedorService.list(session, ativo=ativo)
    return [FornecedorOut.model_validate(f) for f in items]


@router.post("/fornecedores", response_model=FornecedorOut, status_code=201)
async def fornecedor_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    payload: FornecedorCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FornecedorOut:
    try:
        f = await services.FornecedorService.create(session, payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FornecedorOut.model_validate(f)


@router.get("/fornecedores/{fornecedor_id}", response_model=FornecedorOut)
async def fornecedor_detalhe(
    current: CurrentUser,
    fornecedor_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FornecedorOut:
    try:
        f = await services.FornecedorService.get(session, fornecedor_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado") from exc
    return FornecedorOut.model_validate(f)


@router.patch("/fornecedores/{fornecedor_id}", response_model=FornecedorOut)
async def fornecedor_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    fornecedor_id: int,
    payload: FornecedorUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FornecedorOut:
    try:
        f = await services.FornecedorService.get(session, fornecedor_id)
        f = await services.FornecedorService.update(session, f, payload)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FornecedorOut.model_validate(f)


@router.delete("/fornecedores/{fornecedor_id}", status_code=204)
async def fornecedor_deletar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    fornecedor_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        f = await services.FornecedorService.get(session, fornecedor_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado") from exc
    await services.FornecedorService.delete(session, f)
    return None


# ============================ Cotações ============================


@router.get("/cotacoes", response_model=dict)
async def cotacoes_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> dict:
    ev_id = _require_evento(evento_id)
    items, total = await services.CotacaoService.list(
        session, ev_id, status=status, page=page, page_size=page_size
    )
    return {
        "items": [CotacaoOut.model_validate(c).model_dump() for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/cotacoes", response_model=CotacaoOut, status_code=201)
async def cotacao_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    payload: CotacaoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> CotacaoOut:
    ev_id = _require_evento(evento_id)
    try:
        c = await services.CotacaoService.create(session, ev_id, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CotacaoOut.model_validate(c)


@router.get("/cotacoes/{cotacao_id}", response_model=CotacaoOut)
async def cotacao_detalhe(
    current: CurrentUser,
    cotacao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CotacaoOut:
    try:
        c = await services.CotacaoService.get(session, cotacao_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Cotação não encontrada") from exc
    return CotacaoOut.model_validate(c)


@router.patch("/cotacoes/{cotacao_id}", response_model=CotacaoOut)
async def cotacao_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    cotacao_id: int,
    payload: CotacaoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CotacaoOut:
    try:
        c = await services.CotacaoService.get(session, cotacao_id)
        c = await services.CotacaoService.update(session, c, payload, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Cotação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CotacaoOut.model_validate(c)


@router.post("/cotacoes/{cotacao_id}/fechar", response_model=CotacaoOut)
async def cotacao_fechar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    cotacao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CotacaoOut:
    try:
        c = await services.CotacaoService.get(session, cotacao_id)
        c = await services.CotacaoService.fechar(session, c, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Cotação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CotacaoOut.model_validate(c)


@router.post("/cotacoes/{cotacao_id}/cancelar", response_model=CotacaoOut)
async def cotacao_cancelar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    cotacao_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CotacaoOut:
    try:
        c = await services.CotacaoService.get(session, cotacao_id)
        c = await services.CotacaoService.cancelar(session, c)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Cotação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CotacaoOut.model_validate(c)


@router.post("/cotacoes/{cotacao_id}/aprovar", response_model=CotacaoOut)
async def cotacao_aprovar(
    current: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    cotacao_id: int,
    payload: CotacaoAprovarIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CotacaoOut:
    try:
        c = await services.CotacaoService.get(session, cotacao_id)
        c, _lanc, _oc = await services.CotacaoService.aprovar(session, c, payload, current.id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Cotação não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CotacaoOut.model_validate(c)


# ---------------------------------------------------------------------------
# Ordens de Compra
# ---------------------------------------------------------------------------


@router.get("/ordens-compra", response_model=PaginatedOrdensCompra)
async def ordens_compra_lista(
    current: Annotated[CurrentUser, Depends(require_scopes("admin:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedOrdensCompra:
    from app.inventory.models import OrdemCompra
    from sqlalchemy import func, select
    count_q = select(func.count()).select_from(OrdemCompra)
    total = (await session.execute(count_q)).scalar() or 0

    stmt = (
        select(OrdemCompra)
        .order_by(OrdemCompra.criado_em.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()

    out = []
    for oc in items:
        d = OrdemCompraOut.model_validate(oc)
        d.fornecedor_nome = oc.fornecedor.nome if oc.fornecedor else ""
        d.criado_por_nome = f"{oc.criado_por.first_name} {oc.criado_por.last_name}".strip() if oc.criado_por else ""
        d.evento_id = oc.cotacao.evento_id if oc.cotacao else None
        out.append(d)

    return PaginatedOrdensCompra(items=out, total=total, page=page, page_size=page_size)