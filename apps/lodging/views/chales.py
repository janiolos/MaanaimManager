from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.utils import get_evento_atual
from apps.core.permissions import can_read_lodging, can_write_lodging
from apps.lodging.forms import ChaleForm
from apps.lodging.models import Chale, ReservaChale

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
