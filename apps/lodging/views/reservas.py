from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.utils import get_evento_atual
from apps.core.permissions import can_read_lodging, can_write_lodging
from apps.finance.models import CategoriaFinanceira, LancamentoFinanceiro
from apps.lodging.forms import ReservaChaleForm
from apps.lodging.models import Chale, ReservaChale


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
        "reservas": page_obj.object_list, # Make sure the template has "reservas" if it uses it directly without page_obj
    }
    return render(request, "lodging/reservas_lista.html", context)


@login_required
@user_passes_test(can_write_lodging)
def reserva_criar(request):
    evento = get_evento_atual(request)
    chale_id = request.GET.get("chale_id")
    data_entrada = request.GET.get("data_entrada")
    data_saida = request.GET.get("data_saida")
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
        if data_entrada:
            initial["data_entrada"] = data_entrada
        if data_saida:
            initial["data_saida"] = data_saida
        form = ReservaChaleForm(initial=initial, evento=evento)

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
