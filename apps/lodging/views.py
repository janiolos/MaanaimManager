from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.utils import get_evento_atual
from apps.finance.models import CategoriaFinanceira, LancamentoFinanceiro
from apps.core.permissions import can_read_lodging, can_write_lodging
from .forms import ChaleForm, ReservaChaleForm
from .models import Chale, ReservaChale


def _criar_lancamento_hospedagem(reserva, usuario):
    if not reserva.pago or reserva.lancamento_financeiro_id:
        return
    if not reserva.forma_pagamento or not reserva.conta_id:
        return
    categoria, _ = CategoriaFinanceira.objects.get_or_create(
        nome="Hospedagem",
        tipo=CategoriaFinanceira.RECEITA,
    )
    lancamento = LancamentoFinanceiro.objects.create(
        evento=reserva.evento,
        tipo=LancamentoFinanceiro.RECEITA,
        categoria=categoria,
        conta=reserva.conta,
        data=date.today(),
        descricao=f"Hospedagem - {reserva.chale.codigo} - {reserva.responsavel_nome}",
        valor=reserva.valor_adicional,
        forma_pagamento=reserva.forma_pagamento,
        criado_por=usuario,
        atualizado_por=usuario,
    )
    reserva.lancamento_financeiro = lancamento
    reserva.save(update_fields=["lancamento_financeiro"])


@login_required
@user_passes_test(can_read_lodging)
def chales_lista(request):
    evento = get_evento_atual(request)
    chales = list(Chale.objects.all().order_by("codigo"))
    reservas = (
        ReservaChale.objects.filter(evento=evento, status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA])
        .select_related("chale")
    )
    reservas_por_chale = {r.chale_id: r for r in reservas}

    cards = []
    totais = {"disponivel": 0, "reservado": 0, "ocupado": 0, "indisponivel": 0}
    pode_editar = can_write_lodging(request.user)

    for chale in chales:
        reserva = reservas_por_chale.get(chale.id)
        if chale.status != Chale.ATIVO:
            estado = "indisponivel"
            estado_label = "Indisponivel"
            badge_class = "bg-secondary"
        elif reserva and reserva.status == ReservaChale.CONFIRMADA:
            estado = "ocupado"
            estado_label = "Ocupado"
            badge_class = "bg-danger"
        elif reserva and reserva.status == ReservaChale.PRE_RESERVA:
            estado = "reservado"
            estado_label = "Reservado"
            badge_class = "bg-warning"
        else:
            estado = "disponivel"
            estado_label = "Disponivel"
            badge_class = "bg-success"

        totais[estado] += 1

        action_url = None
        if pode_editar:
            if reserva:
                action_url = reverse("lodging:reserva_editar", args=[reserva.id])
            elif chale.status == Chale.ATIVO:
                action_url = f"{reverse('lodging:reserva_criar')}?chale_id={chale.id}"

        cards.append(
            {
                "chale": chale,
                "reserva": reserva,
                "estado": estado,
                "estado_label": estado_label,
                "badge_class": badge_class,
                "action_url": action_url,
                "edit_url": reverse("lodging:chale_editar", args=[chale.id]) if pode_editar else None,
            }
        )

    context = {
        "evento": evento,
        "cards": cards,
        "totais": totais,
        "pode_editar": pode_editar,
    }
    return render(request, "lodging/chales_lista.html", context)


@login_required
@user_passes_test(can_write_lodging)
def chale_criar(request):
    if request.method == "POST":
        form = ChaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Chale criado com sucesso.")
            return redirect(reverse("lodging:chales_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = ChaleForm()
    return render(request, "lodging/chale_form.html", {"form": form, "acao": "Novo"})


@login_required
@user_passes_test(can_write_lodging)
def chale_editar(request, chale_id):
    chale = get_object_or_404(Chale, id=chale_id)
    if request.method == "POST":
        form = ChaleForm(request.POST, instance=chale)
        if form.is_valid():
            form.save()
            messages.success(request, "Chale atualizado com sucesso.")
            return redirect(reverse("lodging:chales_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = ChaleForm(instance=chale)
    return render(request, "lodging/chale_form.html", {"form": form, "acao": "Editar"})


@login_required
@user_passes_test(can_read_lodging)
def reservas_lista(request):
    evento = get_evento_atual(request)
    queryset = (
        ReservaChale.objects.filter(evento=evento)
        .select_related("chale", "evento")
        .order_by("-criado_em")
    )

    status = request.GET.get("status")
    chale = request.GET.get("chale")
    acessivel = request.GET.get("acessivel")

    if status:
        queryset = queryset.filter(status=status)
    if chale:
        queryset = queryset.filter(chale_id=chale)
    if acessivel == "sim":
        queryset = queryset.filter(chale__acessivel_cadeirante=True)
    if acessivel == "nao":
        queryset = queryset.filter(chale__acessivel_cadeirante=False)

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    context = {
        "page_obj": page_obj,
        "filtros": {"status": status or "", "chale": chale or "", "acessivel": acessivel or ""},
        "querystring": query_params.urlencode(),
        "status_choices": ReservaChale.STATUS_CHOICES,
        "chales": Chale.objects.all().order_by("codigo"),
    }
    return render(request, "lodging/reservas_lista.html", context)


@login_required
@user_passes_test(can_write_lodging)
def reserva_criar(request):
    evento = get_evento_atual(request)
    chale_id = request.GET.get("chale_id")
    if request.method == "POST":
        form = ReservaChaleForm(request.POST, evento=evento)
        form.instance.evento = evento
        if form.is_valid():
            with transaction.atomic():
                reserva = form.save(commit=False)
                reserva.evento = evento
                reserva.criado_por = request.user
                reserva.atualizado_por = request.user
                reserva.save()
                _criar_lancamento_hospedagem(reserva, request.user)
            messages.success(request, "Reserva criada com sucesso.")
            return redirect(reverse("lodging:reservas_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        initial = {}
        if chale_id and str(chale_id).isdigit():
            initial["chale"] = int(chale_id)
        form = ReservaChaleForm(initial=initial, evento=evento)

    chales = Chale.objects.all().order_by("codigo")
    chales_disponiveis = form.fields["chale"].queryset.order_by("codigo")
    return render(
        request,
        "lodging/reserva_form.html",
        {"form": form, "acao": "Nova", "chales_disponiveis": chales_disponiveis, "evento": evento},
    )


@login_required
@user_passes_test(can_write_lodging)
def reserva_editar(request, reserva_id):
    evento = get_evento_atual(request)
    reserva = get_object_or_404(ReservaChale, id=reserva_id, evento=evento)
    if request.method == "POST":
        form = ReservaChaleForm(request.POST, instance=reserva, evento=evento)
        if form.is_valid():
            with transaction.atomic():
                reserva = form.save(commit=False)
                reserva.atualizado_por = request.user
                reserva.save()
                _criar_lancamento_hospedagem(reserva, request.user)
            messages.success(request, "Reserva atualizada com sucesso.")
            return redirect(reverse("lodging:reservas_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = ReservaChaleForm(instance=reserva, evento=evento)

    chales_disponiveis = form.fields["chale"].queryset.order_by("codigo")
    return render(
        request,
        "lodging/reserva_form.html",
        {
            "form": form,
            "acao": "Editar",
            "chales_disponiveis": chales_disponiveis,
            "evento": evento,
            "reserva": reserva,
        },
    )


@login_required
@user_passes_test(can_write_lodging)
def reserva_excluir(request, reserva_id):
    evento = get_evento_atual(request)
    reserva = get_object_or_404(ReservaChale, id=reserva_id, evento=evento)
    if request.method == "POST":
        reserva.delete()
        messages.success(request, "Reserva removida com sucesso.")
        return redirect(reverse("lodging:reservas_lista"))
    return render(
        request,
        "lodging/reserva_confirmar_excluir.html",
        {"reserva": reserva},
    )


@login_required
@user_passes_test(can_read_lodging)
def mapa_chales(request):
    evento = get_evento_atual(request)
    chales = Chale.objects.all().order_by("codigo")
    reservas_confirmadas = (
        ReservaChale.objects.filter(evento=evento, status=ReservaChale.CONFIRMADA)
        .select_related("chale")
        .order_by("chale__codigo")
    )
    reservas_map = {reserva.chale_id: reserva for reserva in reservas_confirmadas}

    cards = []
    for chale in chales:
        reserva = reservas_map.get(chale.id)
        if chale.status != Chale.ATIVO:
            estado = "indisponivel"
        elif reserva:
            estado = "ocupado"
        else:
            estado = "livre"
        cards.append({"chale": chale, "reserva": reserva, "estado": estado})

    return render(request, "lodging/mapa_chales.html", {"cards": cards, "evento": evento})
