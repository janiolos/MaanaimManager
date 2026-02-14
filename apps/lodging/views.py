from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date

from apps.core.utils import get_evento_atual
from apps.finance.models import CategoriaFinanceira, LancamentoFinanceiro
from apps.core.permissions import can_read_lodging, can_write_lodging
from .forms import AcaoChaleForm, ChaleForm, ReservaChaleForm
from .models import AcaoChale, Chale, ReservaChale


def _safe_next_url(request, candidate, default_name="lodging:mapa_chales"):
    if candidate and url_has_allowed_host_and_scheme(candidate, {request.get_host()}):
        return candidate
    return reverse(default_name)


@login_required
@user_passes_test(can_read_lodging)
def dashboard(request):
    evento = get_evento_atual(request)
    chales = Chale.objects.all()
    reservas = ReservaChale.objects.filter(evento=evento) if evento else ReservaChale.objects.none()

    contexto = {
        "evento": evento,
        "chales_total": chales.count(),
        "chales_disponiveis": chales.filter(status=Chale.ATIVO).count(),
        "chales_indisponiveis": chales.exclude(status=Chale.ATIVO).count(),
        "reservas_total": reservas.count(),
        "reservas_confirmadas": reservas.filter(status=ReservaChale.CONFIRMADA).count(),
        "reservas_pre": reservas.filter(status=ReservaChale.PRE_RESERVA).count(),
        "pode_editar": can_write_lodging(request.user),
    }
    return render(request, "lodging/dashboard.html", contexto)


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


@login_required
@user_passes_test(can_read_lodging)
def mapa_chales(request):
    evento = get_evento_atual(request)
    chales = Chale.objects.all().order_by("codigo")
    reservas_ativas = (
        ReservaChale.objects.filter(
            evento=evento,
            status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
        )
        .select_related("chale")
        .order_by("chale__codigo")
    )

    reservas_ativas = list(reservas_ativas)
    acoes_ativas = list(
        AcaoChale.objects.filter(evento=evento, ativo=True).select_related("chale")
    ) if evento else []
    reservas_por_chale = {}
    for reserva in reservas_ativas:
        reservas_por_chale.setdefault(reserva.chale_id, []).append(reserva)
    acoes_por_chale = {}
    for acao in acoes_ativas:
        acoes_por_chale.setdefault(acao.chale_id, []).append(acao)

    cards = []
    totais = {"disponivel": 0, "reservado": 0, "ocupado": 0, "indisponivel": 0}
    pode_editar = can_write_lodging(request.user)

    hoje = date.today()
    for chale in chales:
        reservas_chale = reservas_por_chale.get(chale.id, [])
        acoes_chale = acoes_por_chale.get(chale.id, [])
        reserva = None
        for reserva_item in reservas_chale:
            if (
                reserva_item.data_entrada
                and reserva_item.data_saida
                and reserva_item.data_entrada <= hoje < reserva_item.data_saida
            ):
                reserva = reserva_item
                break
        if reserva is None and reservas_chale:
            reserva = reservas_chale[0]

        if chale.status != Chale.ATIVO:
            estado = "indisponivel"
            estado_label = "Indisponivel"
            badge_class = "bg-secondary"
        elif any(acao.data_inicio <= hoje < acao.data_fim for acao in acoes_chale):
            estado = "indisponivel"
            estado_label = "Indisponivel"
            badge_class = "bg-secondary"
        elif (
            reserva
            and reserva.status == ReservaChale.CONFIRMADA
            and reserva.data_entrada
            and reserva.data_saida
            and reserva.data_entrada <= hoje < reserva.data_saida
        ):
            estado = "ocupado"
            estado_label = "Ocupado"
            badge_class = "bg-danger"
        elif reserva and reserva.status in [ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA]:
            estado = "reservado"
            estado_label = "Reservado"
            badge_class = "bg-warning"
        else:
            estado = "disponivel"
            estado_label = "Disponivel"
            badge_class = "bg-success"

        totais[estado] += 1

        action_reserva_url = None
        if pode_editar:
            if reserva:
                action_reserva_url = reverse("lodging:reserva_editar", args=[reserva.id])
            elif chale.status == Chale.ATIVO:
                action_reserva_url = f"{reverse('lodging:reserva_criar')}?chale_id={chale.id}"

        cards.append(
            {
                "chale": chale,
                "reserva": reserva,
                "acoes": sorted(
                    acoes_chale,
                    key=lambda acao: (acao.data_inicio, acao.id),
                ),
                "estado": estado,
                "estado_label": estado_label,
                "badge_class": badge_class,
                "action_reserva_url": action_reserva_url,
            }
        )

    week_start_param = request.GET.get("week_start")
    week_start = parse_date(week_start_param) if week_start_param else None
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    dias_semana = [week_start + timedelta(days=idx) for idx in range(7)]
    timeline_rows = []
    for item in cards:
        cells = []
        for dia in dias_semana:
            estado = "disponivel"
            estado_label = "Disponivel"
            label = "Livre"

            if item["chale"].status != Chale.ATIVO:
                estado = "indisponivel"
                estado_label = "Indisponivel"
                label = item["chale"].get_status_display()
            else:
                for acao in acoes_por_chale.get(item["chale"].id, []):
                    if acao.data_inicio <= dia < acao.data_fim:
                        estado = "indisponivel"
                        estado_label = acao.get_tipo_display()
                        label = acao.titulo
                        break

                if estado == "disponivel":
                    for reserva_dia in reservas_por_chale.get(item["chale"].id, []):
                        if (
                            reserva_dia.status in [ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA]
                            and reserva_dia.data_entrada
                            and reserva_dia.data_saida
                            and reserva_dia.data_entrada <= dia < reserva_dia.data_saida
                        ):
                            if reserva_dia.status == ReservaChale.CONFIRMADA:
                                estado = "ocupado"
                                estado_label = "Ocupado"
                            else:
                                estado = "reservado"
                                estado_label = "Reservado"
                            label = reserva_dia.responsavel_nome
                            break

            cells.append(
                {
                    "dia": dia,
                    "estado": estado,
                    "estado_label": estado_label,
                    "label": label,
                }
            )
        timeline_rows.append(
            {
                "chale": item["chale"],
                "reserva": item["reserva"],
                "estado": item["estado"],
                "cells": cells,
            }
        )

    week_end = week_start + timedelta(days=6)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    return render(
        request,
        "lodging/mapa_chales.html",
        {
            "cards": cards,
            "evento": evento,
            "totais": totais,
            "pode_editar": pode_editar,
            "dias_semana": dias_semana,
            "timeline_rows": timeline_rows,
            "week_start": week_start,
            "week_end": week_end,
            "prev_week": prev_week,
            "next_week": next_week,
            "mapa_return": f"{reverse('lodging:mapa_chales')}?week_start={week_start.isoformat()}",
        },
    )


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


@login_required
@require_POST
@user_passes_test(can_write_lodging)
def chale_status_rapido(request, chale_id):
    evento = get_evento_atual(request)
    chale = get_object_or_404(Chale, id=chale_id)
    acao = request.POST.get("acao")

    if acao == "liberar":
        chale.status = Chale.ATIVO
        chale.save(update_fields=["status"])
        AcaoChale.objects.filter(evento=evento, chale=chale, ativo=True).update(ativo=False)
        messages.success(request, f"{chale.codigo} liberado para reservas e acoes ativas encerradas.")
    elif acao == "cancelar_reserva":
        reserva = ReservaChale.objects.filter(
            evento=evento,
            chale=chale,
            status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
        ).first()
        if reserva:
            reserva.status = ReservaChale.CANCELADA
            reserva.atualizado_por = request.user
            reserva.save(update_fields=["status", "atualizado_por", "atualizado_em"])
            messages.success(request, f"Reserva ativa de {chale.codigo} foi cancelada.")
        else:
            messages.warning(request, "Nao existe reserva ativa para cancelar.")
    else:
        messages.error(request, "Acao invalida.")

    return redirect(reverse("lodging:mapa_chales"))
