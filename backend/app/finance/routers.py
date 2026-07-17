"""Routers do módulo finance - /api/v1/finance/*."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from weasyprint import HTML

from app.auth.dependencies import CurrentUser, EventoAtualId, require_scopes
from app.db.session import get_session
from app.finance import schemas, services
from app.finance.models import LancamentoFinanceiro
from app.finance.schemas import (
    CategoriaFinanceiraCreate,
    CategoriaFinanceiraOut,
    CategoriaFinanceiraUpdate,
    CashFlowOut,
    ConciliacaoOut,
    ContaCaixaCreate,
    ContaCaixaOut,
    ContaCaixaUpdate,
    DashboardKPIs,
    DREOut,
    LancamentoCreate,
    LancamentoOut,
    LancamentoUpdate,
    OfficialReportOut,
    PaginatedLancamentos,
)

router = APIRouter(prefix="/finance", tags=["finance"])


def _require_evento(evento_id: int | None) -> int:
    if evento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum evento selecionado (header X-Evento-Id ausente)",
        )
    return evento_id


# --------------------------- Categorias ---------------------------


@router.get("/categorias", response_model=list[CategoriaFinanceiraOut])
async def categorias_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    tipo: str | None = Query(None, description="RECEITA | DESPESA"),
) -> list[CategoriaFinanceiraOut]:
    items = await services.CategoriaService.list(session, tipo=tipo)
    return [CategoriaFinanceiraOut.model_validate(c) for c in items]


@router.post(
    "/categorias",
    response_model=CategoriaFinanceiraOut,
    status_code=201,
)
async def categoria_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    payload: CategoriaFinanceiraCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoriaFinanceiraOut:
    cat = await services.CategoriaService.create(session, payload.nome, payload.tipo)
    return CategoriaFinanceiraOut.model_validate(cat)


@router.patch("/categorias/{cat_id}", response_model=CategoriaFinanceiraOut)
async def categoria_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    cat_id: int,
    payload: CategoriaFinanceiraUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoriaFinanceiraOut:
    try:
        cat = await services.CategoriaService.get(session, cat_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Categoria não encontrada") from exc
    try:
        cat = await services.CategoriaService.update(session, cat, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    return CategoriaFinanceiraOut.model_validate(cat)


@router.delete("/categorias/{cat_id}", status_code=204)
async def categoria_deletar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    cat_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        cat = await services.CategoriaService.get(session, cat_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Categoria não encontrada") from exc
    await services.CategoriaService.delete(session, cat)
    return None


# --------------------------- Contas ---------------------------


@router.get("/contas", response_model=list[ContaCaixaOut])
async def contas_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    apenas_ativos: bool = True,
) -> list[ContaCaixaOut]:
    items = await services.ContaService.list(session, apenas_ativos=apenas_ativos)
    return [ContaCaixaOut.model_validate(c) for c in items]


@router.post("/contas", response_model=ContaCaixaOut, status_code=201)
async def conta_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    payload: ContaCaixaCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContaCaixaOut:
    conta = await services.ContaService.create(session, payload.nome, payload.ativo)
    return ContaCaixaOut.model_validate(conta)


@router.patch("/contas/{conta_id}", response_model=ContaCaixaOut)
async def conta_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    conta_id: int,
    payload: ContaCaixaUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContaCaixaOut:
    try:
        conta = await services.ContaService.get(session, conta_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Conta não encontrada") from exc
    conta = await services.ContaService.update(session, conta, payload.model_dump(exclude_unset=True))
    return ContaCaixaOut.model_validate(conta)


@router.delete("/contas/{conta_id}", status_code=204)
async def conta_deletar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    conta_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        conta = await services.ContaService.get(session, conta_id)
    except NoResultFound as exc:
        raise HTTPException(404, "Conta não encontrada") from exc
    await services.ContaService.delete(session, conta)
    return None


# --------------------------- Lancamentos ---------------------------


@router.get("/lancamentos", response_model=PaginatedLancamentos)
async def lancamentos_lista(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    tipo: str | None = Query(None),
    categoria_id: int | None = Query(None),
    conta_id: int | None = Query(None),
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedLancamentos:
    ev_id = _require_evento(evento_id)
    from datetime import date as _date

    di = _date.fromisoformat(data_inicio) if data_inicio else None
    df = _date.fromisoformat(data_fim) if data_fim else None

    items, total = await services.LancamentoService.list(
        session,
        ev_id,
        tipo=tipo,
        categoria_id=categoria_id,
        conta_id=conta_id,
        data_inicio=di,
        data_fim=df,
        page=page,
        page_size=page_size,
    )
    return PaginatedLancamentos(
        items=[LancamentoOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/lancamentos", response_model=LancamentoOut, status_code=201)
async def lancamento_criar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    payload: LancamentoCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> LancamentoOut:
    ev_id = _require_evento(evento_id)
    try:
        lanc = await services.LancamentoService.create(session, ev_id, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LancamentoOut.model_validate(lanc)


@router.get("/lancamentos/{lancamento_id}", response_model=LancamentoOut)
async def lancamento_detalhe(
    current: CurrentUser,
    lancamento_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LancamentoOut:
    try:
        lanc = await services.LancamentoService.get(session, lancamento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado") from exc
    return LancamentoOut.model_validate(lanc)


@router.patch("/lancamentos/{lancamento_id}", response_model=LancamentoOut)
async def lancamento_editar(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    lancamento_id: int,
    payload: LancamentoUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LancamentoOut:
    try:
        lanc = await services.LancamentoService.get(session, lancamento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado") from exc
    try:
        await services.LancamentoService.update(session, lanc, payload, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LancamentoOut.model_validate(lanc)


@router.delete("/lancamentos/{lancamento_id}", status_code=204)
async def lancamento_excluir(
    current: Annotated[CurrentUser, Depends(require_scopes("finance:write"))],
    lancamento_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        lanc = await services.LancamentoService.get(session, lancamento_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado") from exc
    await services.LancamentoService.delete(session, lanc)


# --------------------------- Dashboard ---------------------------


@router.get("/dashboard", response_model=DashboardKPIs)
async def dashboard(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
) -> DashboardKPIs:
    ev_id = _require_evento(evento_id)
    data = await services.LancamentoService.dashboard(session, ev_id)
    return DashboardKPIs(**data)


def _parse_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Data inválida: {val}")


def format_currency(val) -> str:
    try:
        return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"


def format_date_br(iso_str: str | None) -> str | None:
    if not iso_str:
        return None
    try:
        parts = iso_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return iso_str


def _render_dre_pdf(data: dict, evento_nome: str) -> str:
    """Gera HTML para o PDF do DRE no formato original do Django (versão 1.0)."""
    rows_rec = "".join(
        f"<tr><td>{r['categoria'] or '(Sem categoria)'}</td><td class='text-right'>{format_currency(r['total'])}</td></tr>"
        for r in data["receitas_por_categoria"]
    )
    if not rows_rec:
        rows_rec = "<tr><td colspan='2' style='text-align: center; color: #777;'>Nenhuma receita no período.</td></tr>"
    else:
        rows_rec += f"<tr><td class='text-strong'>Total de Receitas</td><td class='text-right text-strong text-success'>{format_currency(data['total_receitas'])}</td></tr>"

    rows_desp = "".join(
        f"<tr><td>{r['categoria'] or '(Sem categoria)'}</td><td class='text-right'>{format_currency(r['total'])}</td></tr>"
        for r in data["despesas_por_categoria"]
    )
    if not rows_desp:
        rows_desp = "<tr><td colspan='2' style='text-align: center; color: #777;'>Nenhuma despesa no período.</td></tr>"
    else:
        rows_desp += f"<tr><td class='text-strong'>Total de Despesas</td><td class='text-right text-strong text-danger'>{format_currency(data['total_despesas'])}</td></tr>"

    di_br = format_date_br(data["data_inicio"])
    df_br = format_date_br(data["data_fim"])
    if di_br and df_br:
        periodo_str = f"{di_br} a {df_br}"
    elif di_br:
        periodo_str = f"A partir de {di_br}"
    elif df_br:
        periodo_str = f"Até {df_br}"
    else:
        periodo_str = "Todo o período"

    resultado_liquido = data["resultado_liquido"]
    resultado_class = "text-success" if float(resultado_liquido) >= 0 else "text-danger"

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>DRE - {evento_nome}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 2cm;
      @bottom-right {{
        content: "Página " counter(page) " de " counter(pages);
        font-size: 10pt;
        color: #666;
      }}
    }}

    body {{
      font-family: Arial, sans-serif;
      color: #333;
      font-size: 12pt;
    }}

    h1 {{
      color: #206bc4;
      text-align: center;
      margin-bottom: 5px;
    }}

    .header-info {{
      text-align: center;
      margin-bottom: 30px;
      color: #555;
      font-size: 11pt;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 11pt;
    }}

    th,
    td {{
      padding: 8px 10px;
      border-bottom: 1px solid #e0e0e0;
    }}

    th {{
      background-color: #f8f9fa;
      text-align: left;
      font-weight: bold;
    }}

    .text-right {{
      text-align: right;
    }}

    .text-strong {{
      font-weight: bold;
    }}

    .text-success {{
      color: #2fb344;
    }}

    .text-danger {{
      color: #d63939;
    }}

    .bg-light {{
      background-color: #f8f9fa;
    }}

    .summary-box {{
      border: 1px solid #ddd;
      padding: 15px;
      margin-bottom: 30px;
      border-radius: 4px;
    }}

    .summary-row {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }}

    .summary-row:last-child {{
      margin-bottom: 0;
      padding-top: 10px;
      border-top: 2px solid #ddd;
      font-size: 14pt;
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <h1>Demonstrativo de Resultado do Exercício (DRE)</h1>
  <div class="header-info">
    <strong>Evento:</strong> {evento_nome}<br>
    <strong>Período:</strong> {periodo_str}
  </div>

  <div class="summary-box bg-light">
    <div class="summary-row text-success">
      <span>Total Receitas (+)</span>
      <span>R$ {format_currency(data['total_receitas'])}</span>
    </div>
    <div class="summary-row text-danger">
      <span>Total Despesas (-)</span>
      <span>R$ {format_currency(data['total_despesas'])}</span>
    </div>
    <div class="summary-row {resultado_class}">
      <span>Resultado Líquido</span>
      <span>R$ {format_currency(resultado_liquido)}</span>
    </div>
  </div>

  <h3>Receitas por Categoria</h3>
  <table>
    <thead>
      <tr>
        <th>Categoria</th>
        <th class="text-right">Total (R$)</th>
      </tr>
    </thead>
    <tbody>
      {rows_rec}
    </tbody>
  </table>

  <h3 style="margin-top: 30px;">Despesas por Categoria</h3>
  <table>
    <thead>
      <tr>
        <th>Categoria</th>
        <th class="text-right">Total (R$)</th>
      </tr>
    </thead>
    <tbody>
      {rows_desp}
    </tbody>
  </table>
</body>
</html>"""


@router.get("/relatorios/dre", response_model=DREOut)
async def relatorio_dre(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> DREOut:
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.dre(session, ev_id, data_inicio=di, data_fim=df)
    return DREOut(**data)


@router.get("/relatorios/fluxo-caixa", response_model=CashFlowOut)
async def relatorio_fluxo_caixa(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> CashFlowOut:
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.cash_flow(session, ev_id, data_inicio=di, data_fim=df)
    return CashFlowOut(**data)


@router.get("/relatorios/conciliacao", response_model=ConciliacaoOut)
async def relatorio_conciliacao(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> ConciliacaoOut:
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.reconciliation(session, ev_id, data_inicio=di, data_fim=df)
    return ConciliacaoOut(**data)


@router.get("/relatorios/oficial", response_model=OfficialReportOut)
async def relatorio_oficial(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> OfficialReportOut:
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.official_report(session, ev_id, data_inicio=di, data_fim=df)
    return OfficialReportOut(**data)


@router.get("/relatorios/dre/pdf")
async def relatorio_dre_pdf(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> Response:
    """Exporta DRE como PDF via WeasyPrint."""
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.dre(session, ev_id, data_inicio=di, data_fim=df)
    data["data_inicio"] = data_inicio or ""
    data["data_fim"] = data_fim or ""

    from app.core.models import Evento
    evento = await session.get(Evento, ev_id)
    evento_nome = evento.nome if evento else "Todos"

    html_str = _render_dre_pdf(data, evento_nome)

    try:
        pdf_bytes = HTML(string=html_str).write_pdf()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {exc}")

    filename = f"dre_{ev_id}_{data_inicio or 'inicio'}_{data_fim or 'fim'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/relatorios/dre/csv")
async def relatorio_dre_csv(
    current: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    evento_id: EventoAtualId,
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
) -> Response:
    """Exporta DRE como CSV."""
    ev_id = _require_evento(evento_id)
    di, df = _parse_date(data_inicio), _parse_date(data_fim)
    data = await services.ReportService.dre(session, ev_id, data_inicio=di, data_fim=df)

    from app.core.models import Evento
    evento = await session.get(Evento, ev_id)
    evento_nome = evento.nome if evento else "Todos"

    import csv, io

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM
    writer = csv.writer(buf)
    writer.writerow(["DRE - Demonstrativo de Resultado do Exercicio"])
    writer.writerow([f"Evento: {evento_nome}"])
    writer.writerow([f"Periodo: {data_inicio or '-'} a {data_fim or '-'}"])
    writer.writerow([])
    writer.writerow(["Receitas por Categoria", "Total"])
    for r in data["receitas_por_categoria"]:
        writer.writerow([r["categoria"] or "(Sem categoria)", float(r["total"])])
    writer.writerow(["TOTAL RECEITAS", float(data["total_receitas"])])
    writer.writerow([])
    writer.writerow(["Despesas por Categoria", "Total"])
    for d in data["despesas_por_categoria"]:
        writer.writerow([d["categoria"] or "(Sem categoria)", float(d["total"])])
    writer.writerow(["TOTAL DESPESAS", float(data["total_despesas"])])
    writer.writerow([])
    writer.writerow(["RESULTADO LIQUIDO", float(data["resultado_liquido"])])

    filename = f"dre_{ev_id}_{data_inicio or 'inicio'}_{data_fim or 'fim'}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )