import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Case, When, Value, DecimalField, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.models import ConfiguracaoSistema
from apps.core.permissions import can_read_inventory, can_read_lodging, can_read_notifications
from apps.core.utils import get_evento_atual
from .forms import LancamentoFinanceiroForm, AnexoLancamentoForm
from .models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro, AnexoLancamento
from .permissions import can_read_finance, can_write_finance


@login_required
@user_passes_test(can_read_finance)
def dashboard(request):
    evento = get_evento_atual(request)
    lancamentos = (
        LancamentoFinanceiro.objects.filter(evento=evento)
        .select_related("categoria")
        .order_by("data")
    )

    total_receitas = (
        lancamentos.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"]
        or 0
    )
    total_despesas = (
        lancamentos.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"]
        or 0
    )
    saldo = total_receitas - total_despesas
    qtd_lancamentos = lancamentos.aggregate(total=Count("id"))["total"] or 0

    serie = (
        lancamentos.values("data", "tipo")
        .annotate(total=Sum("valor"))
        .order_by("data")
    )

    labels = []
    receitas = []
    despesas = []
    saldo_acumulado = []
    resumo_por_data = {}
    for item in serie:
        data_str = item["data"].strftime("%d/%m")
        if data_str not in resumo_por_data:
            resumo_por_data[data_str] = {"receita": 0, "despesa": 0}
            labels.append(data_str)
        if item["tipo"] == LancamentoFinanceiro.RECEITA:
            resumo_por_data[data_str]["receita"] = float(item["total"])
        else:
            resumo_por_data[data_str]["despesa"] = float(item["total"])

    saldo_corrente = 0.0
    for data_str in labels:
        valores = resumo_por_data[data_str]
        receitas.append(valores["receita"])
        despesas.append(valores["despesa"])
        saldo_corrente += valores["receita"] - valores["despesa"]
        saldo_acumulado.append(saldo_corrente)

    chart_data = json.dumps(
        {
            "labels": labels,
            "receitas": receitas,
            "despesas": despesas,
            "saldo_acumulado": saldo_acumulado,
        }
    )

    config = ConfiguracaoSistema.get_solo()
    module_kpis = {}

    if config.modulo_estoque_ativo and can_read_inventory(request.user):
        from apps.inventory.models import Produto

        module_kpis["estoque"] = {
            "produtos_total": Produto.objects.count(),
            "alerta_baixo": Produto.objects.filter(estoque_atual__lt=F("estoque_minimo")).count(),
            "alerta_acima": Produto.objects.filter(
                estoque_maximo__gt=0,
                estoque_atual__gt=F("estoque_maximo"),
            ).count(),
        }

    if config.modulo_hospedagem_ativo and can_read_lodging(request.user) and evento:
        from apps.lodging.models import ReservaChale

        module_kpis["hospedagem"] = {
            "reservas_total": ReservaChale.objects.filter(evento=evento).count(),
            "reservas_confirmadas": ReservaChale.objects.filter(
                evento=evento,
                status=ReservaChale.CONFIRMADA,
            ).count(),
        }

    if config.modulo_notificacoes_ativo and can_read_notifications(request.user) and evento:
        from apps.notifications.models import ReminderConfig

        module_kpis["notificacoes"] = {
            "lembretes_ativos": ReminderConfig.objects.filter(evento=evento, ativo=True).count(),
            "lembretes_pendentes": ReminderConfig.objects.filter(
                evento=evento,
                ativo=True,
                enviado=False,
            ).count(),
        }

    context = {
        "evento": evento,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo": saldo,
        "qtd_lancamentos": qtd_lancamentos,
        "chart_data": chart_data,
        "pode_escrever": can_write_finance(request.user),
        "module_kpis": module_kpis,
    }
    return render(request, "dashboard/index.html", context)


@login_required
@user_passes_test(can_read_finance)
def lancamentos_lista(request):
    evento = get_evento_atual(request)
    queryset = (
        LancamentoFinanceiro.objects.filter(evento=evento)
        .select_related("categoria", "conta")
        .order_by("-data", "-id")
    )

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    conta = request.GET.get("conta")
    texto = request.GET.get("texto")

    if data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if categoria:
        queryset = queryset.filter(categoria_id=categoria)
    if conta:
        queryset = queryset.filter(conta_id=conta)
    if texto:
        queryset = queryset.filter(descricao__icontains=texto)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    context = {
        "page_obj": page_obj,
        "categorias": CategoriaFinanceira.objects.all(),
        "contas": ContaCaixa.objects.all(),
        "formas_pagamento": LancamentoFinanceiro.FORMAS_PAGAMENTO,
        "pode_anexos": can_write_finance(request.user),
        "querystring": query_params.urlencode(),
        "filtros": {
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
            "tipo": tipo or "",
            "categoria": categoria or "",
            "conta": conta or "",
            "texto": texto or "",
        },
    }
    return render(request, "finance/lancamentos_lista.html", context)


@login_required
@user_passes_test(can_read_finance)
def categorias_por_tipo(request):
    tipo = request.GET.get("tipo")
    categorias = CategoriaFinanceira.objects.all()
    if tipo:
        categorias = categorias.filter(tipo=tipo)
    data = [{"id": c.id, "nome": c.nome, "tipo": c.tipo} for c in categorias]
    return JsonResponse({"categorias": data})


@login_required
@user_passes_test(can_write_finance)
def lancamento_criar(request):
    evento = get_evento_atual(request)
    return_url = request.GET.get("next")
    if request.method == "POST":
        form = LancamentoFinanceiroForm(request.POST)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.evento = evento
            lancamento.criado_por = request.user
            lancamento.atualizado_por = request.user
            lancamento.save()
            messages.success(request, "Lancamento criado com sucesso.")
            next_url = request.GET.get("next") or return_url
            return redirect(next_url or reverse("finance:lancamentos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = LancamentoFinanceiroForm(initial={"data": date.today()})

    categorias = CategoriaFinanceira.objects.all()
    return render(
        request,
        "finance/lancamento_form.html",
        {
            "form": form,
            "acao": "Novo",
            "categorias": categorias,
            "return_url": return_url,
        },
    )


@login_required
@user_passes_test(can_write_finance)
def lancamento_editar(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    return_url = request.GET.get("next")
    if request.method == "POST":
        form = LancamentoFinanceiroForm(request.POST, instance=lancamento)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.atualizado_por = request.user
            lancamento.save()
            messages.success(request, "Lancamento atualizado com sucesso.")
            next_url = request.GET.get("next") or return_url
            return redirect(next_url or reverse("finance:lancamentos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = LancamentoFinanceiroForm(instance=lancamento)

    categorias = CategoriaFinanceira.objects.all()
    return render(
        request,
        "finance/lancamento_form.html",
        {
            "form": form,
            "acao": "Editar",
            "lancamento": lancamento,
            "categorias": categorias,
            "return_url": return_url,
        },
    )


@login_required
@user_passes_test(can_write_finance)
def lancamento_excluir(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    return_url = request.GET.get("next")
    if request.method == "POST":
        lancamento.delete()
        messages.success(request, "Lancamento excluido com sucesso.")
        next_url = request.GET.get("next") or return_url
        return redirect(next_url or reverse("finance:lancamentos_lista"))
    return render(
        request,
        "finance/lancamento_confirmar_excluir.html",
        {"lancamento": lancamento, "return_url": return_url},
    )


@login_required
@user_passes_test(can_write_finance)
def anexos(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    anexos_qs = AnexoLancamento.objects.filter(lancamento=lancamento)
    return_url = request.GET.get("next")

    if request.method == "POST":
        form = AnexoLancamentoForm(request.POST, request.FILES)
        if form.is_valid():
            anexo = form.save(commit=False)
            anexo.lancamento = lancamento
            anexo.enviado_por = request.user
            anexo.save()
            messages.success(request, "Anexo enviado com sucesso.")
            next_url = request.GET.get("next") or return_url
            return redirect(next_url or reverse("finance:anexos", args=[lancamento.id]))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = AnexoLancamentoForm()

    return render(
        request,
        "finance/lancamento_anexos.html",
        {
            "lancamento": lancamento,
            "anexos": anexos_qs,
            "form": form,
            "return_url": return_url,
        },
    )


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
    lancamentos = LancamentoFinanceiro.objects.filter(evento=evento)

    total_receitas = (
        lancamentos.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"]
        or 0
    )
    total_despesas = (
        lancamentos.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"]
        or 0
    )
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
    queryset = (
        LancamentoFinanceiro.objects.filter(evento=evento)
        .select_related("categoria", "conta", "criado_por")
        .order_by("-data", "-id")
    )

    data_inicio, data_fim = _get_periodo(request)
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    conta = request.GET.get("conta")
    forma_pagamento = request.GET.get("forma_pagamento")
    texto = request.GET.get("texto")

    if data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if categoria:
        queryset = queryset.filter(categoria_id=categoria)
    if conta:
        queryset = queryset.filter(conta_id=conta)
    if forma_pagamento:
        queryset = queryset.filter(forma_pagamento=forma_pagamento)
    if texto:
        queryset = queryset.filter(descricao__icontains=texto)

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
    base = LancamentoFinanceiro.objects.filter(evento=evento)
    if data_inicio:
        base = base.filter(data__gte=data_inicio)
    if data_fim:
        base = base.filter(data__lte=data_fim)

    receitas = (
        base.filter(tipo=LancamentoFinanceiro.RECEITA)
        .values("forma_pagamento")
        .annotate(total=Sum("valor"))
        .order_by("forma_pagamento")
    )
    despesas = (
        base.filter(tipo=LancamentoFinanceiro.DESPESA)
        .values("forma_pagamento")
        .annotate(total=Sum("valor"))
        .order_by("forma_pagamento")
    )

    def to_map(rows):
        return {row["forma_pagamento"]: row["total"] for row in rows}

    receitas_map = to_map(receitas)
    despesas_map = to_map(despesas)
    formas = sorted(set(receitas_map.keys()) | set(despesas_map.keys()))
    formas_label = dict(LancamentoFinanceiro.FORMAS_PAGAMENTO)
    linhas = []
    for forma in formas:
        total_receita = receitas_map.get(forma, 0) or 0
        total_despesa = despesas_map.get(forma, 0) or 0
        linhas.append(
            {
                "forma_pagamento": forma,
                "forma_label": formas_label.get(forma, forma),
                "receitas": total_receita,
                "despesas": total_despesa,
                "saldo": total_receita - total_despesa,
            }
        )

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
    base = LancamentoFinanceiro.objects.filter(evento=evento).order_by("data")
    if data_inicio:
        base = base.filter(data__gte=data_inicio)
    if data_fim:
        base = base.filter(data__lte=data_fim)

    diaria = (
        base.values("data")
        .annotate(
            receitas=Sum(
                Case(
                    When(tipo=LancamentoFinanceiro.RECEITA, then="valor"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            despesas=Sum(
                Case(
                    When(tipo=LancamentoFinanceiro.DESPESA, then="valor"),
                    default=Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
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
        linhas.append(
            {
                "data": item["data"],
                "receitas": receitas,
                "despesas": despesas,
                "saldo_dia": saldo_dia,
                "saldo_acumulado": saldo_acumulado,
            }
        )
        label = item["data"].strftime("%d/%m")
        labels.append(label)
        receitas_series.append(float(receitas))
        despesas_series.append(float(despesas))
        saldo_series.append(float(saldo_acumulado))

    chart_data = json.dumps(
        {
            "labels": labels,
            "receitas": receitas_series,
            "despesas": despesas_series,
            "saldo": saldo_series,
        }
    )

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
    base = LancamentoFinanceiro.objects.filter(evento=evento)
    if data_inicio:
        base = base.filter(data__gte=data_inicio)
    if data_fim:
        base = base.filter(data__lte=data_fim)

    receitas = base.filter(tipo=LancamentoFinanceiro.RECEITA).select_related("categoria").order_by(
        "data", "id"
    )
    despesas = base.filter(tipo=LancamentoFinanceiro.DESPESA).select_related("categoria").order_by(
        "data", "id"
    )
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
