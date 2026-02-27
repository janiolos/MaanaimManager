import json
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Case, When, Value, DecimalField
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from apps.core.utils import get_evento_atual
from apps.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro
from apps.finance.permissions import can_read_finance

logger = logging.getLogger(__name__)

def _get_periodo(request):
    data_inicio = request.GET.get("data_inicio") or request.GET.get("data_ini")
    data_fim = request.GET.get("data_fim")
    return data_inicio, data_fim

@login_required
@user_passes_test(can_read_finance)
def relatorios_index(request):
    return render(request, "finance/reports/index.html")

@login_required
@user_passes_test(can_read_finance)
def relatorio_evento(request):
    evento = get_evento_atual(request)
    lancamentos = LancamentoFinanceiro.objects.filter(evento=evento) if evento else LancamentoFinanceiro.objects.none()

    total_receitas = lancamentos.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"] or 0
    total_despesas = lancamentos.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"] or 0
    saldo = total_receitas - total_despesas
    qtd_lancamentos = lancamentos.aggregate(total=Count("id"))["total"] or 0

    resumo_categorias = (
        lancamentos.values("categoria__nome", "tipo")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    total_geral = sum(item["total"] for item in resumo_categorias)

    context = {
        "evento": evento,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo": saldo,
        "qtd_lancamentos": qtd_lancamentos,
        "resumo_categorias": resumo_categorias,
        "total_geral": total_geral,
    }
    return render(request, "finance/reports/evento_resumo.html", context)

@login_required
@user_passes_test(can_read_finance)
def relatorio_detalhado(request):
    evento = get_evento_atual(request)
    queryset = LancamentoFinanceiro.objects.all().select_related("categoria", "conta", "criado_por").order_by("-data", "-id")
    if evento:
        queryset = queryset.filter(evento=evento)

    data_inicio, data_fim = _get_periodo(request)
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    conta = request.GET.get("conta")
    forma_pagamento = request.GET.get("forma_pagamento")
    texto = request.GET.get("texto")

    if data_inicio: queryset = queryset.filter(data__gte=data_inicio)
    if data_fim: queryset = queryset.filter(data__lte=data_fim)
    if tipo: queryset = queryset.filter(tipo=tipo)
    if categoria: queryset = queryset.filter(categoria_id=categoria)
    if conta: queryset = queryset.filter(conta_id=conta)
    if forma_pagamento: queryset = queryset.filter(forma_pagamento=forma_pagamento)
    if texto: queryset = queryset.filter(descricao__icontains=texto)

    queryset = queryset.annotate(qtd_anexos=Count("anexolancamento"))

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    context = {
        "page_obj": page_obj,
        "categorias": CategoriaFinanceira.objects.all(),
        "contas": ContaCaixa.objects.all(),
        "querystring": query_params.urlencode(),
        "filtros": {
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
            "tipo": tipo or "",
            "categoria": categoria or "",
            "conta": conta or "",
            "forma_pagamento": forma_pagamento or "",
            "texto": texto or "",
        },
    }
    return render(request, "finance/reports/detalhado.html", context)

@login_required
@user_passes_test(can_read_finance)
def relatorio_conciliacao(request):
    evento = get_evento_atual(request)
    data_inicio, data_fim = _get_periodo(request)
    base = LancamentoFinanceiro.objects.all()
    if evento: base = base.filter(evento=evento)
    if data_inicio: base = base.filter(data__gte=data_inicio)
    if data_fim: base = base.filter(data__lte=data_fim)

    receitas = base.filter(tipo=LancamentoFinanceiro.RECEITA).values("forma_pagamento").annotate(total=Sum("valor")).order_by("forma_pagamento")
    despesas = base.filter(tipo=LancamentoFinanceiro.DESPESA).values("forma_pagamento").annotate(total=Sum("valor")).order_by("forma_pagamento")

    def to_map(rows): return {r["forma_pagamento"]: r["total"] for r in rows}
    
    receitas_map = to_map(receitas)
    despesas_map = to_map(despesas)
    formas = sorted(set(receitas_map.keys()) | set(despesas_map.keys()))
    formas_label = dict(LancamentoFinanceiro.FORMAS_PAGAMENTO)
    linhas = []
    
    for forma in formas:
        total_rec = receitas_map.get(forma, 0) or 0
        total_des = despesas_map.get(forma, 0) or 0
        linhas.append({
            "forma_pagamento": forma,
            "forma_label": formas_label.get(forma, forma),
            "receitas": total_rec,
            "despesas": total_des,
            "saldo": total_rec - total_des,
        })

    context = {
        "evento": evento,
        "data_inicio": data_inicio or "",
        "data_fim": data_fim or "",
        "linhas": linhas,
    }
    return render(request, "finance/reports/conciliacao.html", context)

@login_required
@user_passes_test(can_read_finance)
def relatorio_fluxo_caixa(request):
    evento = get_evento_atual(request)
    data_inicio, data_fim = _get_periodo(request)
    base = LancamentoFinanceiro.objects.all().order_by("data")
    if evento: base = base.filter(evento=evento)
    if data_inicio: base = base.filter(data__gte=data_inicio)
    if data_fim: base = base.filter(data__lte=data_fim)

    diaria = (
        base.values("data")
        .annotate(
            receitas=Sum(Case(When(tipo=LancamentoFinanceiro.RECEITA, then="valor"), default=Value(0), output_field=DecimalField(max_digits=12, decimal_places=2))),
            despesas=Sum(Case(When(tipo=LancamentoFinanceiro.DESPESA, then="valor"), default=Value(0), output_field=DecimalField(max_digits=12, decimal_places=2))),
        )
        .order_by("data")
    )

    linhas = []
    saldo_acumulado = 0
    labels = []
    receitas_series = []
    despesas_series = []
    saldo_series = []
    
    for item in diaria:
        receitas = item["receitas"] or 0
        despesas = item["despesas"] or 0
        saldo_dia = receitas - despesas
        saldo_acumulado += saldo_dia
        linhas.append({
            "data": item["data"],
            "receitas": receitas,
            "despesas": despesas,
            "saldo_dia": saldo_dia,
            "saldo_acumulado": saldo_acumulado,
        })
        labels.append(item["data"].strftime("%d/%m"))
        receitas_series.append(float(receitas))
        despesas_series.append(float(despesas))
        saldo_series.append(float(saldo_acumulado))

    chart_data = json.dumps({
        "labels": labels,
        "receitas": receitas_series,
        "despesas": despesas_series,
        "saldo": saldo_series,
    })

    context = {
        "evento": evento,
        "data_inicio": data_inicio or "",
        "data_fim": data_fim or "",
        "linhas": linhas,
        "chart_data": chart_data,
    }
    return render(request, "finance/reports/fluxo_caixa.html", context)


@login_required
@user_passes_test(can_read_finance)
def relatorio_pdf(request):
    evento = get_evento_atual(request)
    data_inicio, data_fim = _get_periodo(request)
    base = LancamentoFinanceiro.objects.all()
    if evento: base = base.filter(evento=evento)
    if data_inicio: base = base.filter(data__gte=data_inicio)
    if data_fim: base = base.filter(data__lte=data_fim)

    receitas = base.filter(tipo=LancamentoFinanceiro.RECEITA).select_related("categoria").order_by("data", "id")
    despesas = base.filter(tipo=LancamentoFinanceiro.DESPESA).select_related("categoria").order_by("data", "id")
    total_receitas = receitas.aggregate(total=Sum("valor"))["total"] or 0
    total_despesas = despesas.aggregate(total=Sum("valor"))["total"] or 0
    saldo = total_receitas - total_despesas

    context = {
        "evento": evento,
        "data_inicio": data_inicio or "",
        "data_fim": data_fim or "",
        "receitas": receitas,
        "despesas": despesas,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo": saldo,
    }
    return render(request, "finance/reports/relatorio_pdf.html", context)


@login_required
@user_passes_test(can_read_finance)
def relatorio_dre(request):
    """DRE — Demonstrativo de Resultado do Exercicio. Reescrito do zero."""
    context = {"erro": None}

    try:
        evento = get_evento_atual(request)
        context["evento"] = evento

        data_inicio = request.GET.get("data_inicio", "").strip() or None
        data_fim    = request.GET.get("data_fim",    "").strip() or None
        context["data_inicio"] = data_inicio or ""
        context["data_fim"]    = data_fim    or ""

        qs = LancamentoFinanceiro.objects.all()
        if evento is not None:
            qs = qs.filter(evento=evento)
        if data_inicio:
            qs = qs.filter(data__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data__lte=data_fim)

        total_receitas = qs.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(t=Sum("valor"))["t"] or 0
        total_despesas = qs.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(t=Sum("valor"))["t"] or 0
        resultado_liquido = total_receitas - total_despesas

        try:
            margem = (float(resultado_liquido) / float(total_receitas)) * 100 if total_receitas else None
        except Exception:
            margem = None

        receitas_por_categoria = list(qs.filter(tipo=LancamentoFinanceiro.RECEITA).values("categoria__nome").annotate(total=Sum("valor")).order_by("-total"))
        despesas_por_categoria = list(qs.filter(tipo=LancamentoFinanceiro.DESPESA).values("categoria__nome").annotate(total=Sum("valor")).order_by("-total"))

        context.update({
            "total_receitas":        total_receitas,
            "total_despesas":        total_despesas,
            "resultado_liquido":     resultado_liquido,
            "margem_percentual":     margem,
            "receitas_por_categoria": receitas_por_categoria,
            "despesas_por_categoria": despesas_por_categoria,
        })

    except Exception as exc:
        logger.exception("Erro inesperado no DRE: %s", exc)
        context["erro"] = str(exc)

    return render(request, "finance/reports/dre.html", context)

@login_required
@user_passes_test(can_read_finance)
def relatorio_dre_pdf(request):
    messages.error(request, "Exportacao PDF nao disponivel. Use CSV/Excel.")
    return redirect(reverse("finance:relatorio_dre"))

@login_required
@user_passes_test(can_read_finance)
def relatorio_dre_excel(request):
    import csv
    from django.utils.encoding import smart_str
    try:
        evento = get_evento_atual(request)
        data_inicio = request.GET.get("data_inicio", "").strip() or None
        data_fim    = request.GET.get("data_fim",    "").strip() or None

        qs = LancamentoFinanceiro.objects.all()
        if evento is not None: qs = qs.filter(evento=evento)
        if data_inicio: qs = qs.filter(data__gte=data_inicio)
        if data_fim: qs = qs.filter(data__lte=data_fim)

        receitas = list(qs.filter(tipo=LancamentoFinanceiro.RECEITA).values("categoria__nome").annotate(total=Sum("valor")).order_by("-total"))
        despesas = list(qs.filter(tipo=LancamentoFinanceiro.DESPESA).values("categoria__nome").annotate(total=Sum("valor")).order_by("-total"))
        
        total_receitas = sum(r["total"] for r in receitas if r["total"]) or 0
        total_despesas = sum(d["total"] for d in despesas if d["total"]) or 0

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        evento_id = getattr(evento, "id", "all")
        filename  = f"dre_{evento_id}_{data_inicio or 'inicio'}_{data_fim or 'fim'}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([smart_str("DRE - Demonstrativo de Resultado do Exercicio")])
        writer.writerow([smart_str(f"Evento: {getattr(evento, 'nome', 'Todos')}")])
        writer.writerow([smart_str(f"Periodo: {data_inicio or '-'} a {data_fim or '-'}")])
        writer.writerow([])
        writer.writerow(["Receitas por Categoria", "Total"])
        for r in receitas: writer.writerow([smart_str(r["categoria__nome"] or "(Sem categoria)"), float(r["total"])])
        writer.writerow(["TOTAL RECEITAS", float(total_receitas)])
        writer.writerow([])
        writer.writerow(["Despesas por Categoria", "Total"])
        for d in despesas: writer.writerow([smart_str(d["categoria__nome"] or "(Sem categoria)"), float(d["total"])])
        writer.writerow(["TOTAL DESPESAS", float(total_despesas)])
        writer.writerow([])
        writer.writerow(["RESULTADO LIQUIDO", float(total_receitas - total_despesas)])
        return response
    except Exception as exc:
        logger.exception("Erro ao exportar DRE CSV: %s", exc)
        messages.error(request, f"Erro ao exportar CSV: {exc}")
        return redirect(reverse("finance:relatorio_dre"))
