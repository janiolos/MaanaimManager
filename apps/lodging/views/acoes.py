from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.utils import get_evento_atual
from apps.core.permissions import can_write_lodging
from apps.lodging.forms import AcaoChaleForm
from apps.lodging.models import AcaoChale


def _safe_next_url(request, candidate, default_name="lodging:mapa_chales"):
    if candidate and url_has_allowed_host_and_scheme(candidate, {request.get_host()}):
        return candidate
    return reverse(default_name)


@login_required
@user_passes_test(can_write_lodging)
def acao_criar(request):
    evento = get_evento_atual(request)
    next_url = _safe_next_url(request, request.POST.get("next") or request.GET.get("next"))
    if request.method == "POST":
        form = AcaoChaleForm(request.POST)
        if form.is_valid():
            acao = form.save(commit=False)
            acao.evento = evento
            acao.criado_por = request.user
            acao.atualizado_por = request.user
            acao.save()
            messages.success(request, "Acao de chale registrada com sucesso.")
            return redirect(next_url)
        messages.error(request, "Corrija os erros do formulario.")
    else:
        initial = {
            "chale": request.GET.get("chale_id"),
            "tipo": request.GET.get("tipo"),
            "data_inicio": request.GET.get("data_inicio"),
            "data_fim": request.GET.get("data_fim"),
            "ativo": True,
        }
        form = AcaoChaleForm(initial=initial)

    return render(
        request,
        "lodging/acao_form.html",
        {"form": form, "acao": "Nova", "next": next_url},
    )


@login_required
@user_passes_test(can_write_lodging)
def acao_editar(request, acao_id):
    evento = get_evento_atual(request)
    acao = get_object_or_404(AcaoChale, id=acao_id, evento=evento)
    next_url = _safe_next_url(request, request.POST.get("next") or request.GET.get("next"))
    if request.method == "POST":
        form = AcaoChaleForm(request.POST, instance=acao)
        if form.is_valid():
            acao = form.save(commit=False)
            acao.evento = evento
            acao.atualizado_por = request.user
            acao.save()
            messages.success(request, "Acao de chale atualizada com sucesso.")
            return redirect(next_url)
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = AcaoChaleForm(instance=acao)

    return render(
        request,
        "lodging/acao_form.html",
        {"form": form, "acao": "Editar", "next": next_url, "acao_obj": acao},
    )


@login_required
@require_POST
@user_passes_test(can_write_lodging)
def acao_excluir(request, acao_id):
    evento = get_evento_atual(request)
    acao = get_object_or_404(AcaoChale, id=acao_id, evento=evento)
    next_url = _safe_next_url(request, request.POST.get("next"))
    titulo = acao.titulo
    acao.delete()
    messages.success(request, f"Acao '{titulo}' removida com sucesso.")
    return redirect(next_url)
