import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.permissions import (
    can_manage_core,
    can_read_core,
    can_read_finance,
    can_read_inventory,
    can_read_lodging,
    can_read_notifications,
)
from apps.core.utils import get_evento_atual
from .forms import EventoForm
from .models import Evento


@login_required
def home(request):
    if can_read_finance(request.user):
        return redirect("finance:dashboard")
    if can_read_inventory(request.user):
        return redirect("inventory:produtos_lista")
    if can_read_lodging(request.user):
        return redirect("lodging:chales_lista")
    if can_read_notifications(request.user):
        return redirect("notifications:lembretes_lista")
    return redirect("core:eventos_lista")


@login_required
def selecionar_evento(request):
    eventos = Evento.objects.filter(ativo=True).order_by("-data_inicio")
    if request.method == "POST":
        evento_id = request.POST.get("evento_id")
        if evento_id and eventos.filter(id=evento_id).exists():
            request.session["evento_id"] = int(evento_id)
            messages.success(request, "Ciclo selecionado com sucesso.")
            default_next = reverse("core:eventos_lista")
            if can_read_finance(request.user):
                default_next = reverse("finance:dashboard")
            elif can_read_inventory(request.user):
                default_next = reverse("inventory:produtos_lista")
            elif can_read_lodging(request.user):
                default_next = reverse("lodging:chales_lista")
            elif can_read_notifications(request.user):
                default_next = reverse("notifications:lembretes_lista")
            return redirect(request.GET.get("next") or default_next)
        messages.error(request, "Selecione um ciclo valido.")
    return render(request, "core/selecionar_evento.html", {"eventos": eventos})


@login_required
@user_passes_test(can_read_core)
def eventos_lista(request):
    eventos = Evento.objects.all().order_by("-data_inicio")
    eventos_calendario = json.dumps(
        [
            {
                "title": evento.nome,
                "start": evento.data_inicio.isoformat(),
                "end": evento.data_fim.isoformat(),
            }
            for evento in eventos
        ]
    )
    return render(
        request,
        "core/eventos_lista.html",
        {"eventos": eventos, "eventos_calendario": eventos_calendario},
    )


@login_required
@user_passes_test(can_manage_core)
def evento_criar(request):
    if request.method == "POST":
        form = EventoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento criado com sucesso.")
            return redirect(reverse("core:eventos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = EventoForm()
    return render(request, "core/evento_form.html", {"form": form, "acao": "Novo"})


@login_required
@user_passes_test(can_manage_core)
def evento_editar(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if evento.fechado:
        messages.error(request, "Evento fechado nao pode ser editado.")
        return redirect(reverse("core:eventos_lista"))

    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento atualizado com sucesso.")
            return redirect(reverse("core:eventos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = EventoForm(instance=evento)
    return render(
        request,
        "core/evento_form.html",
        {"form": form, "acao": "Editar", "evento": evento},
    )


@login_required
def api_health(request):
    return JsonResponse({"status": "ok", "service": "eventa", "version": "mvp"})


@login_required
def api_dashboard(request):
    evento = get_evento_atual(request)
    payload = {
        "evento": None,
        "financeiro": {"receitas": 0, "despesas": 0},
        "estoque": {"produtos": 0, "alertas_baixo": 0},
        "hospedagem": {"reservas": 0},
    }
    if evento:
        payload["evento"] = {
            "id": evento.id,
            "nome": evento.nome,
            "status": evento.status,
            "data_inicio": evento.data_inicio.isoformat() if evento.data_inicio else None,
            "data_fim": evento.data_fim.isoformat() if evento.data_fim else None,
        }

        try:
            from django.db.models import Sum
            from apps.finance.models import LancamentoFinanceiro

            base = LancamentoFinanceiro.objects.filter(evento=evento)
            payload["financeiro"]["receitas"] = float(
                base.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"] or 0
            )
            payload["financeiro"]["despesas"] = float(
                base.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"] or 0
            )
        except Exception:
            pass

        try:
            from apps.inventory.models import Produto

            produtos = list(Produto.objects.all())
            payload["estoque"]["produtos"] = len(produtos)
            payload["estoque"]["alertas_baixo"] = len([p for p in produtos if p.status_estoque == "BAIXO"])
        except Exception:
            pass

        try:
            from apps.lodging.models import ReservaChale

            payload["hospedagem"]["reservas"] = ReservaChale.objects.filter(evento=evento).count()
        except Exception:
            pass

    return JsonResponse(payload)
