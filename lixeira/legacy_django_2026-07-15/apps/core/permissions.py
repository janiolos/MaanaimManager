from django.contrib.auth.models import Group


ROLE_ADMIN = "ADMINISTRADOR"
ROLE_FINANCEIRO = "FINANCEIRO"
ROLE_FINANCEIRO_LEITURA = "FINANCEIRO_LEITURA"
ROLE_ESTOQUE = "ESTOQUE"
ROLE_ESTOQUE_LEITURA = "ESTOQUE_LEITURA"
ROLE_HOSPEDAGEM = "HOSPEDAGEM"
ROLE_HOSPEDAGEM_LEITURA = "HOSPEDAGEM_LEITURA"
ROLE_MENSAGENS = "MENSAGENS"
ROLE_MENSAGENS_LEITURA = "MENSAGENS_LEITURA"
ROLE_COORDENADOR = "COORDENADOR"
ROLE_VISUALIZACAO = "VISUALIZACAO"

# Compatibilidade com grupos legados do projeto
LEGACY_ADMIN = "ADMIN"
LEGACY_FINANCEIRO = "TESOURARIA"
LEGACY_VISUALIZACAO = "LEITURA"


def user_in_groups(user, group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Group.objects.filter(name__in=group_names, user=user).exists()


def can_manage_core(user):
    return user_in_groups(
        user,
        [ROLE_ADMIN, ROLE_COORDENADOR, LEGACY_ADMIN],
    )


def can_read_core(user):
    return user.is_authenticated


def can_write_finance(user):
    return user_in_groups(
        user,
        [ROLE_ADMIN, ROLE_FINANCEIRO, ROLE_COORDENADOR, LEGACY_ADMIN, LEGACY_FINANCEIRO],
    )


def can_read_finance(user):
    return user_in_groups(
        user,
        [
            ROLE_ADMIN,
            ROLE_FINANCEIRO,
            ROLE_FINANCEIRO_LEITURA,
            ROLE_COORDENADOR,
            LEGACY_ADMIN,
            LEGACY_FINANCEIRO,
        ],
    )


def can_write_inventory(user):
    return user_in_groups(user, [ROLE_ADMIN, ROLE_ESTOQUE, ROLE_COORDENADOR, LEGACY_ADMIN])


def can_read_inventory(user):
    return user_in_groups(
        user,
        [ROLE_ADMIN, ROLE_ESTOQUE, ROLE_ESTOQUE_LEITURA, ROLE_COORDENADOR, LEGACY_ADMIN],
    )


def can_write_lodging(user):
    return user_in_groups(user, [ROLE_ADMIN, ROLE_HOSPEDAGEM, ROLE_COORDENADOR, LEGACY_ADMIN])


def can_read_lodging(user):
    return user_in_groups(
        user,
        [
            ROLE_ADMIN,
            ROLE_HOSPEDAGEM,
            ROLE_HOSPEDAGEM_LEITURA,
            ROLE_COORDENADOR,
            LEGACY_ADMIN,
        ],
    )


def can_write_notifications(user):
    return user_in_groups(user, [ROLE_ADMIN, ROLE_MENSAGENS, ROLE_COORDENADOR, LEGACY_ADMIN])


def can_read_notifications(user):
    return user_in_groups(
        user,
        [
            ROLE_ADMIN,
            ROLE_MENSAGENS,
            ROLE_MENSAGENS_LEITURA,
            ROLE_COORDENADOR,
            LEGACY_ADMIN,
        ],
    )
