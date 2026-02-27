from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from apps.core.utils import get_evento_atual
from apps.core.permissions import can_read_lodging, can_write_lodging
from apps.lodging.models import Chale, ReservaChale

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
