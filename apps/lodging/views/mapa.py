from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from apps.core.utils import get_evento_atual
from apps.core.permissions import can_read_lodging, can_write_lodging
from apps.lodging.models import AcaoChale, Chale, ReservaChale


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
