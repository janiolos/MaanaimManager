from django.db.utils import OperationalError, ProgrammingError

from .models import ConfiguracaoSistema
from .permissions import (
    can_read_finance,
    can_read_inventory,
    can_read_lodging,
    can_read_notifications,
)
from .utils import get_evento_atual


def evento_atual(request):
    try:
        config = ConfiguracaoSistema.get_solo()
    except (OperationalError, ProgrammingError):
        config = ConfiguracaoSistema(
            nome_sistema="Eventa",
            rotulo_evento_singular="Evento",
            rotulo_evento_plural="Eventos",
            modulo_financeiro_ativo=True,
            modulo_estoque_ativo=True,
            modulo_hospedagem_ativo=True,
            modulo_notificacoes_ativo=True,
        )
    return {
        "evento_atual": get_evento_atual(request),
        "sistema_config": config,
        "rotulo_evento_singular": config.rotulo_evento_singular,
        "rotulo_evento_plural": config.rotulo_evento_plural,
        "modulos_ativos": {
            "financeiro": config.modulo_financeiro_ativo,
            "estoque": config.modulo_estoque_ativo,
            "hospedagem": config.modulo_hospedagem_ativo,
            "notificacoes": config.modulo_notificacoes_ativo,
        },
        "acesso_modulos": {
            "financeiro": can_read_finance(request.user),
            "estoque": can_read_inventory(request.user),
            "hospedagem": can_read_lodging(request.user),
            "notificacoes": can_read_notifications(request.user),
        },
    }
