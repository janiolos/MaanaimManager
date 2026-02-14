from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.core.permissions import can_read_inventory, can_write_inventory
from apps.core.utils import get_evento_atual

from .forms import EntradaEstoqueForm, MovimentoEstoqueForm, ProdutoForm
from .models import EntradaEstoque, MovimentoEstoque, Produto


@login_required
@user_passes_test(can_read_inventory)
def dashboard(request):
    evento = get_evento_atual(request)
    produtos = Produto.objects.all()
    movimentos_evento = MovimentoEstoque.objects.filter(evento=evento) if evento else MovimentoEstoque.objects.none()

    total_estoque = produtos.aggregate(total=Sum("estoque_atual"))["total"] or 0
    contexto = {
        "evento": evento,
        "produtos_total": produtos.count(),
        "alerta_baixo": produtos.filter(estoque_atual__lt=F("estoque_minimo")).count(),
        "alerta_acima": produtos.filter(estoque_maximo__gt=0, estoque_atual__gt=F("estoque_maximo")).count(),
        "total_estoque": total_estoque,
        "movimentos_evento": movimentos_evento.count(),
        "pode_editar": can_write_inventory(request.user),
    }
    return render(request, "inventory/dashboard.html", contexto)


@login_required
@user_passes_test(can_read_inventory)
def produtos_lista(request):
    queryset = Produto.objects.order_by("nome")
    status = request.GET.get("status")
    busca = request.GET.get("busca")

    if busca:
        queryset = queryset.filter(nome__icontains=busca)
    if status == "baixo":
        queryset = [p for p in queryset if p.status_estoque == "BAIXO"]
    elif status == "acima":
        queryset = [p for p in queryset if p.status_estoque == "ACIMA"]

    if not isinstance(queryset, list):
        queryset = list(queryset)

    paginator = Paginator(queryset, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    totais = {
        "total": len(queryset),
        "baixo": len([p for p in queryset if p.status_estoque == "BAIXO"]),
        "acima": len([p for p in queryset if p.status_estoque == "ACIMA"]),
    }

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(
        request,
        "inventory/produtos_lista.html",
        {
            "page_obj": page_obj,
            "totais": totais,
            "filtros": {"status": status or "", "busca": busca or ""},
            "querystring": query_params.urlencode(),
            "pode_editar": can_write_inventory(request.user),
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def produto_criar(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso.")
            return redirect(reverse("inventory:produtos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = ProdutoForm()

    return render(
        request,
        "inventory/produto_form.html",
        {"form": form, "acao": "Novo"},
    )


@login_required
@user_passes_test(can_write_inventory)
def entrada_criar(request):
    if request.method == "POST":
        form = EntradaEstoqueForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                entrada = form.save(commit=False)
                entrada.criado_por = request.user
                entrada.save()
                Produto.objects.filter(pk=entrada.produto_id).update(
                    estoque_atual=F("estoque_atual") + entrada.quantidade
                )
            messages.success(request, "Entrada registrada com sucesso.")
            return redirect(reverse("inventory:produtos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = EntradaEstoqueForm(initial={"data": date.today()})

    return render(
        request,
        "inventory/entrada_form.html",
        {"form": form},
    )


@login_required
@user_passes_test(can_write_inventory)
def movimentacao_criar(request):
    evento = get_evento_atual(request)
    if request.method == "POST":
        form = MovimentoEstoqueForm(request.POST)
        if form.is_valid():
            movimento = form.save(commit=False)
            movimento.evento = evento
            produto = movimento.produto

            if movimento.tipo == MovimentoEstoque.SAIDA and produto.estoque_atual < movimento.quantidade:
                form.add_error("quantidade", "Estoque insuficiente para esta saida.")
            else:
                with transaction.atomic():
                    movimento.criado_por = request.user
                    movimento.save()
                    if movimento.tipo == MovimentoEstoque.SAIDA:
                        Produto.objects.filter(pk=produto.pk).update(
                            estoque_atual=F("estoque_atual") - movimento.quantidade
                        )
                    else:
                        Produto.objects.filter(pk=produto.pk).update(
                            estoque_atual=F("estoque_atual") + movimento.quantidade
                        )
                messages.success(request, "Movimentacao registrada com sucesso.")
                return redirect(reverse("inventory:movimentos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = MovimentoEstoqueForm(initial={"data": date.today()})

    return render(
        request,
        "inventory/movimento_form.html",
        {"form": form, "evento": evento},
    )


@login_required
@user_passes_test(can_read_inventory)
def movimentos_lista(request):
    evento = get_evento_atual(request)
    queryset = MovimentoEstoque.objects.filter(evento=evento).select_related("produto", "evento").order_by("-data", "-id")
    tipo = request.GET.get("tipo")

    if tipo:
        queryset = queryset.filter(tipo=tipo)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(
        request,
        "inventory/movimentos_lista.html",
        {
            "page_obj": page_obj,
            "evento": evento,
            "filtros": {"tipo": tipo or ""},
            "querystring": query_params.urlencode(),
        },
    )
