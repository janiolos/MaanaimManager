import json
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F
from django.shortcuts import render
from apps.core.models import ConfiguracaoSistema
from apps.core.permissions import can_read_inventory, can_read_lodging, can_read_notifications
from apps.core.utils import get_evento_atual
from apps.finance.models import LancamentoFinanceiro
from apps.finance.permissions import can_read_finance, can_write_finance

@login_required
@user_passes_test(can_read_finance)
def dashboard(request):
    evento = get_evento_atual(request)

    base_qs = LancamentoFinanceiro.objects.all()
    if evento:
        base_qs = base_qs.filter(evento=evento)

    total_receitas = base_qs.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"] or 0
    total_despesas = base_qs.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"] or 0
    saldo = total_receitas - total_despesas
    qtd_lancamentos = base_qs.count()

    # Dados do Grafico (ultimos 30 dias com movimento / agrupado por data)
    hoje = date.today()
    lancamentos_chart = base_qs.filter(data__lte=hoje).order_by("data")
    
    resumo_por_data = {}
    for item in lancamentos_chart.values("data", "tipo").annotate(total=Sum("valor")):
        data_str = item["data"].strftime("%Y-%m-%d")
        if data_str not in resumo_por_data:
            resumo_por_data[data_str] = {"receita": 0.0, "despesa": 0.0}
        
        if item["tipo"] == LancamentoFinanceiro.RECEITA:
            resumo_por_data[data_str]["receita"] = float(item["total"])
        else:
            resumo_por_data[data_str]["despesa"] = float(item["total"])

    labels = sorted(list(resumo_por_data.keys()))[-30:] # Ultimos 30 dias com dados
    
    receitas = []
    despesas = []
    saldo_acumulado = []
    
    saldo_corrente = 0.0
    # Obter o saldo acumulado antes das datas que vamos mostrar
    if labels and evento:
        data_inicial_grafico = labels[0]
        lancamentos_anteriores = base_qs.filter(data__lt=data_inicial_grafico)
        receitas_ant = lancamentos_anteriores.filter(tipo=LancamentoFinanceiro.RECEITA).aggregate(total=Sum("valor"))["total"] or 0
        despesas_ant = lancamentos_anteriores.filter(tipo=LancamentoFinanceiro.DESPESA).aggregate(total=Sum("valor"))["total"] or 0
        saldo_corrente = float(receitas_ant - despesas_ant)

    for data_str in labels:
        valores = resumo_por_data.get(data_str, {"receita": 0.0, "despesa": 0.0})
        receitas.append(valores["receita"])
        despesas.append(valores["despesa"])
        saldo_corrente += (valores["receita"] - valores["despesa"])
        saldo_acumulado.append(saldo_corrente)

    chart_data = json.dumps({
        "labels": labels,
        "receitas": receitas,
        "despesas": despesas,
        "saldo_acumulado": saldo_acumulado
    })

    # KPIs de outros modulos
    config = ConfiguracaoSistema.get_solo()
    module_kpis = {}

    if config.modulo_estoque_ativo and can_read_inventory(request.user):
        from apps.inventory.models import Produto
        module_kpis["estoque"] = {
            "produtos_total": Produto.objects.count(),
            "alerta_baixo": Produto.objects.filter(estoque_atual__lt=F("estoque_minimo")).count(),
            "alerta_acima": Produto.objects.filter(estoque_maximo__gt=0, estoque_atual__gt=F("estoque_maximo")).count()
        }

    if config.modulo_hospedagem_ativo and can_read_lodging(request.user) and evento:
        from apps.lodging.models import ReservaChale
        module_kpis["hospedagem"] = {
            "reservas_total": ReservaChale.objects.filter(evento=evento).count(),
            "reservas_confirmadas": ReservaChale.objects.filter(evento=evento, status=ReservaChale.CONFIRMADA).count()
        }

    if config.modulo_notificacoes_ativo and can_read_notifications(request.user) and evento:
        from apps.notifications.models import ReminderConfig
        module_kpis["notificacoes"] = {
            "lembretes_ativos": ReminderConfig.objects.filter(evento=evento, ativo=True).count(),
            "lembretes_pendentes": ReminderConfig.objects.filter(evento=evento, ativo=True, enviado=False).count()
        }

    context = {
        "evento": evento,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo": saldo,
        "qtd_lancamentos": qtd_lancamentos,
        "chart_data": chart_data,
        "pode_escrever": can_write_finance(request.user),
        "module_kpis": module_kpis
    }
    
    return render(request, "dashboard/index.html", context)
