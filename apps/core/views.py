import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Count, F
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
from .forms import EventoForm, LoginForm
from .models import ConfiguracaoSistema, Evento


class LoginDashboardView(LoginView):
    authentication_form = LoginForm

    def get_success_url(self):
        return reverse("home")


@login_required
def home(request):
    config = ConfiguracaoSistema.get_solo()
    evento = get_evento_atual(request)

    modulos = []

    if config.modulo_financeiro_ativo and can_read_finance(request.user):
        totais = {"receitas": 0, "despesas": 0}
        if evento:
            from django.db.models import Sum
            from apps.finance.models import LancamentoFinanceiro

            base = LancamentoFinanceiro.objects.filter(evento=evento)
            totais["receitas"] = float(
                base.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"] or 0
            )
            totais["despesas"] = float(
                base.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"] or 0
            )
        modulos.append(
            {
                "nome": "Financeiro",
                "descricao": "Fluxo de caixa, lancamentos e relatorios por ciclo.",
                "icone": "ti ti-wallet",
                "cor": "finance",
                "url": reverse("finance:dashboard"),
                "resumo": f"Receitas: R$ {totais['receitas']:.2f} | Despesas: R$ {totais['despesas']:.2f}",
            }
        )

    if config.modulo_estoque_ativo and can_read_inventory(request.user):
        from apps.inventory.models import Produto

        produtos = Produto.objects.count()
        abaixo = Produto.objects.filter(estoque_atual__lt=F("estoque_minimo")).count()
        modulos.append(
            {
                "nome": "Estoque",
                "descricao": "Produtos, entradas e movimentacoes do ciclo atual.",
                "icone": "ti ti-package",
                "cor": "inventory",
                "url": reverse("inventory:dashboard"),
                "resumo": f"Produtos: {produtos} | Alertas: {abaixo}",
            }
        )

    if config.modulo_hospedagem_ativo and can_read_lodging(request.user):
        from apps.lodging.models import Chale, ReservaChale

        reservas = ReservaChale.objects.filter(evento=evento).count() if evento else 0
        modulos.append(
            {
                "nome": "Hospedagem",
                "descricao": "Status dos chales, reservas e ocupacao.",
                "icone": "ti ti-home",
                "cor": "lodging",
                "url": reverse("lodging:dashboard"),
                "resumo": f"Chales: {Chale.objects.count()} | Reservas: {reservas}",
            }
        )

    if config.modulo_notificacoes_ativo and can_read_notifications(request.user):
        from apps.notifications.models import ReminderConfig

        ativos = ReminderConfig.objects.filter(evento=evento, ativo=True).count() if evento else 0
        modulos.append(
            {
                "nome": "Lembretes",
                "descricao": "Agendamento e envio de mensagens via WhatsApp.",
                "icone": "ti ti-bell",
                "cor": "notifications",
                "url": reverse("notifications:dashboard"),
                "resumo": f"Lembretes ativos: {ativos}",
            }
        )

    modulos.append(
        {
            "nome": "Core",
            "descricao": "Configuracoes gerais e gestao de ciclos.",
            "icone": "ti ti-settings",
            "cor": "core",
            "url": reverse("core:dashboard"),
            "resumo": "Acesso a eventos, configuracoes e controle central.",
        }
    )

    return render(
        request,
        "dashboard/home.html",
        {
            "evento": evento,
            "modulos": modulos,
            "qtd_modulos": len(modulos),
        },
    )


@login_required
@user_passes_test(can_read_core)
def dashboard(request):
    eventos = Evento.objects.all()
    contexto = {
        "total_eventos": eventos.count(),
        "eventos_ativos": eventos.filter(ativo=True).count(),
        "eventos_encerrados": eventos.filter(status=Evento.ENCERRADO).count(),
        "distribuicao_status": list(
            eventos.values("status").annotate(total=Count("id")).order_by("status")
        ),
        "pode_gerenciar": can_manage_core(request.user),
    }
    return render(request, "core/dashboard.html", contexto)


@login_required
def selecionar_evento(request):
    eventos = Evento.objects.filter(ativo=True).order_by("-data_inicio")
    if request.method == "POST":
        evento_id = request.POST.get("evento_id")
        if evento_id and eventos.filter(id=evento_id).exists():
            request.session["evento_id"] = int(evento_id)
            messages.success(request, "Ciclo selecionado com sucesso.")
            default_next = reverse("home")
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
