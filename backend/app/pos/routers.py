"""Routers do módulo POS - /api/v1/pos/*."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import CurrentUser, EventoAtualId, require_scopes
from app.db.session import get_session
from app.finance.models import LancamentoFinanceiro
from app.pos.models import (
    EntradaEstoqueLocal,
    FamiliaVenda,
    ItemVendaMobile,
    LocalVenda,
    PagamentoVenda,
    ProdutoLocal,
    VendaMobile,
)
from app.pos.schemas import (
    EntradaEstoqueLocalCreate,
    EntradaEstoqueLocalOut,
    FamiliaVendaCreate,
    FamiliaVendaOut,
    LocalVendaCreate,
    LocalVendaOut,
    LocalVendaUpdate,
    PaginatedVendas,
    PDVDashboard,
    ProdutoLocalCreate,
    ProdutoLocalOut,
    ProdutoLocalUpdate,
    TransferenciaEstoqueLocalCreate,
    TransferenciaEstoqueLocalOut,
    VendaCreate,
    VendaOut,
)
from app.pos.services import TransferenciaEstoqueLocalService, VendaService

router = APIRouter(prefix="/pos", tags=["pos"])


def _require_evento(evento_id: int | None) -> int:
    if evento_id is None:
        raise HTTPException(status_code=400, detail="Header X-Evento-Id obrigatório")
    return evento_id


async def _get_local(session: AsyncSession, local_id: int) -> LocalVenda:
    local = (
        await session.execute(
            select(LocalVenda).where(LocalVenda.id == local_id)
        )
    ).scalar_one_or_none()
    if local is None:
        raise HTTPException(404, "Local não encontrado")
    return local


async def _ensure_nome_local_disponivel(
    session: AsyncSession, nome: str, *, ignore_id: int | None = None
) -> None:
    nome_normalizado = nome.strip().lower()
    stmt = select(LocalVenda).where(func.lower(LocalVenda.nome) == nome_normalizado)
    if ignore_id is not None:
        stmt = stmt.where(LocalVenda.id != ignore_id)
    existente = (await session.execute(stmt)).scalar_one_or_none()
    if existente is not None:
        raise HTTPException(400, "Já existe um local de venda com este nome")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=PDVDashboard)
async def pos_dashboard(
    user: CurrentUser,
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
    local_id: int | None = Query(default=None),
    mes: str | None = Query(default=None),
):
    from decimal import Decimal
    from app.core.models import Evento
    from app.inventory.models import Produto

    eid = _require_evento(evento_id)

    # 1. Fetch matching sales for KPIs and Vendas tab
    stmt = (
        select(VendaMobile)
        .options(
            selectinload(VendaMobile.itens)
            .selectinload(ItemVendaMobile.produto_local)
            .selectinload(ProdutoLocal.produto),
            selectinload(VendaMobile.pagamentos),
        )
        .where(VendaMobile.evento_id == eid)
    )
    if local_id is not None:
        stmt = stmt.where(VendaMobile.local_id == local_id)
    if mes is not None and mes != "Todos":
        stmt = stmt.where(func.extract("month", VendaMobile.data_hora) == int(mes))

    vendas = (await session.execute(stmt)).scalars().unique().all()

    # 2. Fetch products for Estoque tab
    prod_stmt = (
        select(ProdutoLocal)
        .join(LocalVenda, ProdutoLocal.local_id == LocalVenda.id)
        .options(
            selectinload(ProdutoLocal.produto),
            selectinload(ProdutoLocal.familia),
        )
        .where(LocalVenda.evento_id == eid)
    )
    if local_id is not None:
        prod_stmt = prod_stmt.where(ProdutoLocal.local_id == local_id)

    produtos_local = (await session.execute(prod_stmt)).scalars().all()

    # --- Calculations ---
    # Visão Geral KPIs
    receita_total = sum(v.total for v in vendas)
    itens_vendidos = sum(sum(item.quantidade for item in v.itens) for v in vendas)
    itens_estoque = sum(p.estoque_atual for p in produtos_local)
    valor_estoque_venda = sum(p.estoque_atual * p.preco_venda for p in produtos_local)

    # Faturamento por Evento (R$)
    evt_stmt = (
        select(Evento.nome, func.sum(VendaMobile.total))
        .join(VendaMobile, Evento.id == VendaMobile.evento_id)
    )
    if local_id is not None:
        evt_stmt = evt_stmt.where(VendaMobile.local_id == local_id)
    if mes is not None and mes != "Todos":
        evt_stmt = evt_stmt.where(func.extract("month", VendaMobile.data_hora) == int(mes))
    evt_stmt = evt_stmt.group_by(Evento.nome)

    evt_rows = (await session.execute(evt_stmt)).all()
    faturamento_por_evento = {r[0]: Decimal(str(r[1])) for r in evt_rows}

    # Vendas por Mês (R$)
    mes_stmt = (
        select(func.extract("month", VendaMobile.data_hora), func.sum(VendaMobile.total))
        .where(VendaMobile.evento_id == eid)
    )
    if local_id is not None:
        mes_stmt = mes_stmt.where(VendaMobile.local_id == local_id)
    mes_stmt = mes_stmt.group_by(func.extract("month", VendaMobile.data_hora))

    mes_rows = (await session.execute(mes_stmt)).all()
    nomes_meses_abrev = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }
    vendas_por_mes = {}
    for r in mes_rows:
        m_idx = int(r[0])
        if m_idx in nomes_meses_abrev:
            vendas_por_mes[nomes_meses_abrev[m_idx]] = Decimal(str(r[1]))

    # Top/Bottom 10 mais/menos vendidos (Qtd e Receita)
    qtd_por_prod = {}
    rec_por_prod = {}
    for pl in produtos_local:
        if pl.produto:
            qtd_por_prod[pl.produto.nome] = 0
            rec_por_prod[pl.produto.nome] = Decimal("0.00")

    for v in vendas:
        for item in v.itens:
            nome = item.nome_produto
            if nome not in qtd_por_prod:
                qtd_por_prod[nome] = 0
                rec_por_prod[nome] = Decimal("0.00")
            qtd_por_prod[nome] += item.quantidade
            rec_por_prod[nome] += item.total_item

    sorted_prods = sorted(qtd_por_prod.keys(), key=lambda k: qtd_por_prod[k], reverse=True)
    top_10_mais_vendidos = [
        {"nome": name, "qtd": qtd_por_prod[name], "receita": rec_por_prod[name]}
        for name in sorted_prods[:10]
    ]

    sorted_prods_asc = sorted(qtd_por_prod.keys(), key=lambda k: qtd_por_prod[k])
    top_10_menos_vendidos = [
        {"nome": name, "qtd": qtd_por_prod[name], "receita": rec_por_prod[name]}
        for name in sorted_prods_asc[:10]
    ]

    # Vendas Tab KPIs
    total_vendas = len(vendas)
    ticket_medio = receita_total / total_vendas if total_vendas > 0 else Decimal("0.00")

    custo_total_vendas = Decimal("0.00")
    for v in vendas:
        for item in v.itens:
            custo_unit = Decimal("0.00")
            if item.produto_local and item.produto_local.produto:
                custo_unit = item.produto_local.produto.custo_medio_atual
            custo_total_vendas += custo_unit * item.quantidade

    lucro_liquido = receita_total - custo_total_vendas

    # Vendas por Pagamento (R$)
    vendas_por_pagamento = {"DINHEIRO": Decimal("0.00"), "DÉBITO": Decimal("0.00"), "CRÉDITO": Decimal("0.00"), "PIX": Decimal("0.00")}
    for v in vendas:
        for p in v.pagamentos:
            tipo = p.tipo.upper()
            if tipo in vendas_por_pagamento:
                vendas_por_pagamento[tipo] += p.valor

    # Receita por Família (R$)
    receita_por_familia = {}
    for v in vendas:
        for item in v.itens:
            fam = item.familia_produto or "Sem Família"
            receita_por_familia[fam] = receita_por_familia.get(fam, Decimal("0.00")) + item.total_item

    # Top 10 Margem de Lucro (%)
    margem_por_produto = []
    for pl in produtos_local:
        if pl.produto and pl.preco_venda > 0 and pl.produto.custo_medio_atual > 0:
            margem = ((pl.preco_venda - pl.produto.custo_medio_atual) / pl.produto.custo_medio_atual) * 100
            margem_por_produto.append({
                "nome": pl.produto.nome,
                "margem": margem
            })
    top_10_margem_lucro = sorted(margem_por_produto, key=lambda x: x["margem"], reverse=True)[:10]

    # Estoque Tab KPIs
    custo_total_estoque = sum(p.estoque_atual * (p.produto.custo_medio_atual if p.produto else 0) for p in produtos_local)
    valor_potencial_venda = valor_estoque_venda

    # Estoque por Família (Qtd e Custo)
    estoque_por_familia_qtd = {}
    custo_por_familia_valor = {}
    for pl in produtos_local:
        fam = pl.familia.nome if pl.familia else "Sem Família"
        custo = pl.produto.custo_medio_atual if pl.produto else Decimal("0.00")
        estoque_por_familia_qtd[fam] = estoque_por_familia_qtd.get(fam, Decimal("0.00")) + pl.estoque_atual
        custo_por_familia_valor[fam] = custo_por_familia_valor.get(fam, Decimal("0.00")) + (pl.estoque_atual * custo)

    # Produtos com Baixo Estoque
    produtos_baixo_estoque = []
    for pl in produtos_local:
        if pl.produto and pl.estoque_atual <= pl.ponto_reabastecimento:
            status = "Ruptura de Estoque" if pl.estoque_atual < pl.estoque_minimo else "Reabastecer"
            produtos_baixo_estoque.append({
                "codigo": pl.produto.sku or str(pl.produto.id),
                "nome": pl.produto.nome,
                "familia": pl.familia.nome if pl.familia else "Sem Família",
                "status": status,
                "estoque": pl.estoque_atual
            })
    produtos_baixo_estoque = sorted(produtos_baixo_estoque, key=lambda x: x["estoque"])

    return PDVDashboard(
        total_vendas_hoje=receita_total,
        quantidade_vendas_hoje=total_vendas,
        ticket_medio=ticket_medio,
        top_produtos=top_10_mais_vendidos,
        vendas_por_pagamento=vendas_por_pagamento,

        receita_total=receita_total,
        itens_vendidos=itens_vendidos,
        itens_estoque=itens_estoque,
        valor_estoque_venda=valor_estoque_venda,
        faturamento_por_evento=faturamento_por_evento,
        vendas_por_mes=vendas_por_mes,
        top_10_mais_vendidos=top_10_mais_vendidos,
        top_10_menos_vendidos=top_10_menos_vendidos,

        lucro_liquido=lucro_liquido,
        receita_operacional=receita_total,
        total_vendas=total_vendas,
        receita_por_familia=receita_por_familia,
        ranking_mais_vendidos=top_10_mais_vendidos,
        top_10_margem_lucro=top_10_margem_lucro,

        custo_total_estoque=custo_total_estoque,
        itens_fisicos_totais=itens_estoque,
        valor_potencial_venda=valor_potencial_venda,
        estoque_por_familia_qtd=estoque_por_familia_qtd,
        custo_por_familia_valor=custo_por_familia_valor,
        produtos_baixo_estoque=produtos_baixo_estoque,
    )



# ---------------------------------------------------------------------------
# Locais de Venda
# ---------------------------------------------------------------------------


@router.get("/locais", response_model=list[LocalVendaOut])
async def listar_locais(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    apenas_ativos: bool = Query(default=True),
):
    stmt = select(LocalVenda)
    if apenas_ativos:
        stmt = stmt.where(LocalVenda.ativo.is_(True))
    result = await session.execute(stmt.order_by(LocalVenda.nome))
    return result.scalars().all()


@router.post("/locais", response_model=LocalVendaOut, status_code=201)
async def criar_local(
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: LocalVendaCreate,
):
    await _ensure_nome_local_disponivel(session, payload.nome)
    local = LocalVenda(evento_id=None, criado_em=datetime.now(UTC), **payload.model_dump())
    session.add(local)
    await session.flush()
    await session.refresh(local)
    return local


@router.patch("/locais/{local_id}", response_model=LocalVendaOut)
async def atualizar_local(
    local_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: LocalVendaUpdate,
):
    local = await _get_local(session, local_id)
    data = payload.model_dump(exclude_unset=True)
    if "nome" in data:
        await _ensure_nome_local_disponivel(session, data["nome"], ignore_id=local_id)
    for k, v in data.items():
        setattr(local, k, v)
    await session.flush()
    await session.refresh(local)
    return local


@router.post("/locais/{local_id}/abrir-caixa", response_model=LocalVendaOut)
async def abrir_caixa(
    local_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    evento_atual_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from app.pos.models import TurnoCaixa
    if not evento_atual_id:
        raise HTTPException(400, "É necessário selecionar um evento ativo para abrir o caixa")
        
    local = await _get_local(session, local_id)
    if local.caixa_aberto:
        raise HTTPException(400, "Caixa já está aberto")
    
    turno = TurnoCaixa(
        local_id=local_id,
        evento_id=evento_atual_id,
        aberto_em=datetime.now(UTC),
        aberto_por_id=user.id,
        valor_abertura=0.0,
        fechado=False,
    )
    session.add(turno)
    await session.flush()
    
    local.caixa_aberto = True
    local.caixa_aberto_em = turno.aberto_em
    local.caixa_aberto_por_id = user.id
    local.caixa_atual_turno_id = turno.id
    await session.flush()
    await session.refresh(local)
    return local


@router.post("/locais/{local_id}/fechar-caixa", response_model=LocalVendaOut)
async def fechar_caixa(
    local_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from app.pos.finance_integration import POSFinanceIntegration
    try:
        local = await POSFinanceIntegration.consolidar_turno_e_fechar(
            session=session,
            local_id=local_id,
            user_id=user.id,
        )
        return local
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao fechar caixa: {e}")


@router.get("/locais/{local_id}/caixa-atual")
async def obter_resumo_caixa_atual(
    local_id: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    local = await _get_local(session, local_id)
    if not local.caixa_aberto or not local.caixa_atual_turno_id:
        return {
            "caixa_aberto": False,
            "aberto_em": None,
            "total_vendas": 0,
            "soma_total": 0.0,
            "por_forma": {},
        }

    stmt = select(VendaMobile).where(
        VendaMobile.turno_id == local.caixa_atual_turno_id,
    )
    result = await session.execute(stmt)
    vendas = result.scalars().all()

    total_vendas = len(vendas)
    soma_total = float(sum(v.total for v in vendas))

    por_forma = {}
    for v in vendas:
        for p in v.pagamentos:
            tipo = p.tipo
            por_forma[tipo] = por_forma.get(tipo, 0.0) + float(p.valor)

    return {
        "caixa_aberto": True,
        "aberto_em": local.caixa_aberto_em,
        "total_vendas": total_vendas,
        "soma_total": soma_total,
        "por_forma": por_forma,
    }


# ---------------------------------------------------------------------------
# Famílias de Produtos
# ---------------------------------------------------------------------------


@router.get("/locais/{local_id}/familias", response_model=list[FamiliaVendaOut])
async def listar_familias(
    local_id: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await _get_local(session, local_id)
    result = await session.execute(
        select(FamiliaVenda).where(FamiliaVenda.local_id == local_id).order_by(FamiliaVenda.nome)
    )
    return result.scalars().all()


@router.post("/locais/{local_id}/familias", response_model=FamiliaVendaOut, status_code=201)
async def criar_familia(
    local_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: FamiliaVendaCreate,
):
    await _get_local(session, local_id)
    familia = FamiliaVenda(local_id=local_id, nome=payload.nome)
    session.add(familia)
    await session.flush()
    await session.refresh(familia)
    return familia


@router.delete("/locais/{local_id}/familias/{familia_id}", status_code=204)
async def deletar_familia(
    local_id: int,
    familia_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await _get_local(session, local_id)
    familia = await session.get(FamiliaVenda, familia_id)
    if familia is None or familia.local_id != local_id:
        raise HTTPException(404, "Família não encontrada")
    await session.delete(familia)
    await session.flush()
    return None


# ---------------------------------------------------------------------------
# Produtos no Local (Sub-estoque)
# ---------------------------------------------------------------------------


@router.get("/locais/{local_id}/produtos", response_model=list[ProdutoLocalOut])
async def listar_produtos_local(
    local_id: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await _get_local(session, local_id)
    result = await session.execute(
        select(ProdutoLocal)
        .options(
            selectinload(ProdutoLocal.produto),
            selectinload(ProdutoLocal.familia),
        )
        .where(ProdutoLocal.local_id == local_id)
        .order_by(ProdutoLocal.produto_id)
    )
    items = result.scalars().all()
    out = []
    for pl in items:
        d = ProdutoLocalOut.model_validate(pl)
        d.produto_nome = pl.produto.nome if pl.produto else ""
        d.produto_sku = pl.produto.sku if pl.produto else ""
        d.familia_nome = pl.familia.nome if pl.familia else ""
        out.append(d)
    return out


@router.post("/locais/{local_id}/produtos", response_model=ProdutoLocalOut, status_code=201)
async def criar_produto_local(
    local_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: ProdutoLocalCreate,
):
    await _get_local(session, local_id)
    data = payload.model_dump()
    if payload.estoque_atual != 0:
        raise HTTPException(400, "Saldo inicial deve ser zero; use uma transferência")
    if payload.familia_id is not None:
        familia = await session.get(FamiliaVenda, payload.familia_id)
        if familia is None or familia.local_id != local_id:
            raise HTTPException(400, "Família não pertence ao local")
    pl = ProdutoLocal(local_id=local_id, **data)
    session.add(pl)
    await session.flush()
    await session.refresh(pl)
    return pl


@router.patch("/produtos-locais/{pl_id}", response_model=ProdutoLocalOut)
async def atualizar_produto_local(
    pl_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: ProdutoLocalUpdate,
):
    pl = (await session.execute(
        select(ProdutoLocal).where(ProdutoLocal.id == pl_id)
    )).scalar_one_or_none()
    if pl is None:
        raise HTTPException(404, "ProdutoLocal não encontrado")
    if payload.familia_id is not None:
        familia = await session.get(FamiliaVenda, payload.familia_id)
        if familia is None or familia.local_id != pl.local_id:
            raise HTTPException(400, "Família não pertence ao local")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(pl, k, v)
    await session.flush()
    await session.refresh(pl)
    return pl


@router.delete("/produtos-locais/{pl_id}", status_code=204)
async def deletar_produto_local(
    pl_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    pl = (await session.execute(
        select(ProdutoLocal).where(ProdutoLocal.id == pl_id)
    )).scalar_one_or_none()
    if pl is None:
        raise HTTPException(404, "ProdutoLocal não encontrado")
    await session.delete(pl)
    await session.flush()
    return None


# ---------------------------------------------------------------------------
# Entradas de Estoque Local
# ---------------------------------------------------------------------------


@router.get("/locais/{local_id}/entradas", response_model=list[EntradaEstoqueLocalOut])
async def listar_entradas(
    local_id: int,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await _get_local(session, local_id)
    result = await session.execute(
        select(EntradaEstoqueLocal)
        .join(ProdutoLocal, EntradaEstoqueLocal.produto_local_id == ProdutoLocal.id)
        .where(ProdutoLocal.local_id == local_id)
        .order_by(EntradaEstoqueLocal.criado_em.desc())
        .limit(100)
    )
    return result.scalars().all()


@router.post("/entradas", response_model=EntradaEstoqueLocalOut, status_code=201)
async def criar_entrada(
    user: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: EntradaEstoqueLocalCreate,
):
    raise HTTPException(
        status_code=410,
        detail="Entrada direta desativada; use /pos/transferencias para preservar o saldo central",
    )


@router.post("/transferencias", response_model=TransferenciaEstoqueLocalOut, status_code=201)
async def criar_transferencia(
    user: Annotated[CurrentUser, Depends(require_scopes("inventory:write"))],
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: TransferenciaEstoqueLocalCreate,
):
    try:
        return await TransferenciaEstoqueLocalService.criar(
            session,
            evento_id=_require_evento(evento_id),
            user_id=user.id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ---------------------------------------------------------------------------
# Vendas
# ---------------------------------------------------------------------------


@router.get("/vendas", response_model=PaginatedVendas)
async def listar_vendas(
    user: CurrentUser,
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    local_id: int | None = None,
    familia: str | None = Query(default=None),
    produto: str | None = Query(default=None),
):
    eid = _require_evento(evento_id)
    base = select(VendaMobile).where(VendaMobile.evento_id == eid)
    count_base = select(func.count()).select_from(VendaMobile).where(VendaMobile.evento_id == eid)
    if local_id is not None:
        base = base.where(VendaMobile.local_id == local_id)
        count_base = count_base.where(VendaMobile.local_id == local_id)

    item_filters = []
    if familia:
        item_filters.append(ItemVendaMobile.familia_produto == familia)
    if produto:
        termo = f"%{produto.strip()}%"
        item_filters.append(
            or_(
                ItemVendaMobile.nome_produto.ilike(termo),
                ItemVendaMobile.codigo_produto.ilike(termo),
            )
        )
    if item_filters:
        base = base.join(ItemVendaMobile, ItemVendaMobile.venda_id == VendaMobile.id).where(*item_filters).distinct()
        count_base = (
            select(func.count(func.distinct(VendaMobile.id)))
            .select_from(VendaMobile)
            .join(ItemVendaMobile, ItemVendaMobile.venda_id == VendaMobile.id)
            .where(VendaMobile.evento_id == eid, *item_filters)
        )
        if local_id is not None:
            count_base = count_base.where(VendaMobile.local_id == local_id)

    total = (await session.execute(count_base)).scalar_one()
    offset = (page - 1) * page_size
    result = await session.execute(
        base.options(selectinload(VendaMobile.itens), selectinload(VendaMobile.pagamentos))
        .order_by(VendaMobile.data_hora.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedVendas(items=items, total=total, page=page, page_size=page_size)


@router.delete("/vendas/{venda_id}", status_code=204)
async def deletar_venda(
    venda_id: int,
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(VendaMobile)
        .options(selectinload(VendaMobile.itens), selectinload(VendaMobile.pagamentos))
        .where(VendaMobile.id == venda_id, VendaMobile.evento_id == _require_evento(evento_id))
    )
    venda = result.scalars().unique().first()
    if venda is None:
        raise HTTPException(404, "Venda não encontrada")

    if venda.turno_id:
        from app.pos.models import TurnoCaixa
        turno = await session.get(TurnoCaixa, venda.turno_id)
        if turno and turno.fechado:
            raise HTTPException(400, "Não é possível excluir uma venda de um caixa já fechado")

    for item in venda.itens:
        if item.produto_local_id is None:
            continue
        pl = (
            await session.execute(
                select(ProdutoLocal)
                .where(ProdutoLocal.id == item.produto_local_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if pl is not None:
            pl.estoque_atual += item.quantidade

    lancamentos = (
        await session.execute(
            select(LancamentoFinanceiro).where(
                LancamentoFinanceiro.evento_id == venda.evento_id,
                LancamentoFinanceiro.setor_origem == "pos",
                LancamentoFinanceiro.descricao.ilike(f"%Venda PDV #{venda.id_referencia[:8]}%"),
            )
        )
    ).scalars().all()
    for lancamento in lancamentos:
        await session.delete(lancamento)

    for pagamento in list(venda.pagamentos):
        await session.delete(pagamento)
    for item in list(venda.itens):
        await session.delete(item)
    await session.delete(venda)
    await session.flush()
    return None


@router.post("/vendas", response_model=VendaOut, status_code=201)
async def criar_venda(
    user: Annotated[CurrentUser, Depends(require_scopes("pos:write"))],
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: VendaCreate,
):
    eid = _require_evento(evento_id)
    try:
        venda = await VendaService.criar(
            session, evento_id=eid, vendedor_id=user.id, payload=payload
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return venda


@router.get("/vendas/{venda_id}", response_model=VendaOut)
async def obter_venda(
    venda_id: int,
    user: CurrentUser,
    evento_id: EventoAtualId,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(VendaMobile)
        .options(selectinload(VendaMobile.itens), selectinload(VendaMobile.pagamentos))
        .where(VendaMobile.id == venda_id, VendaMobile.evento_id == _require_evento(evento_id))
    )
    venda = result.scalars().unique().first()
    if venda is None:
        raise HTTPException(404, "Venda não encontrada")
    return venda
