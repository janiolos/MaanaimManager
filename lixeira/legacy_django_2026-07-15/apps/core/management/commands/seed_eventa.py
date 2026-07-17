from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.models import CentroCusto, ConfiguracaoSistema, Evento
from apps.core.permissions import (
    ROLE_ADMIN,
    ROLE_COORDENADOR,
    ROLE_ESTOQUE,
    ROLE_ESTOQUE_LEITURA,
    ROLE_FINANCEIRO,
    ROLE_FINANCEIRO_LEITURA,
    ROLE_HOSPEDAGEM,
    ROLE_HOSPEDAGEM_LEITURA,
    ROLE_MENSAGENS,
    ROLE_MENSAGENS_LEITURA,
    ROLE_VISUALIZACAO,
)
from apps.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro
from apps.inventory.models import MovimentoEstoque, Produto
from apps.lodging.models import Chale, ReservaChale


class Command(BaseCommand):
    help = "Popula dados iniciais do MVP Eventa"

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_groups()
        admin_user = self._seed_users()
        config = ConfiguracaoSistema.get_solo()
        config.nome_sistema = "Eventa"
        config.rotulo_evento_singular = "Evento"
        config.rotulo_evento_plural = "Eventos"
        config.modulo_financeiro_ativo = True
        config.modulo_estoque_ativo = True
        config.modulo_hospedagem_ativo = True
        config.modulo_notificacoes_ativo = True
        config.save()

        centro, _ = CentroCusto.objects.get_or_create(codigo="CC-001", defaults={"nome": "Operacao Principal"})

        inicio = timezone.make_aware(datetime.now().replace(hour=8, minute=0, second=0, microsecond=0))
        fim = inicio + timedelta(days=2)
        evento, _ = Evento.objects.get_or_create(
            nome="Ciclo Exemplo Eventa",
            defaults={
                "data_inicio": inicio,
                "data_fim": fim,
                "status": Evento.EM_ANDAMENTO,
                "ativo": True,
                "fechado": False,
                "centro_custo": centro,
                "responsavel_geral": admin_user,
            },
        )

        conta, _ = ContaCaixa.objects.get_or_create(nome="Caixa Geral", defaults={"ativo": True})
        cat_inscricao, _ = CategoriaFinanceira.objects.get_or_create(
            nome="Inscricoes", tipo=CategoriaFinanceira.RECEITA
        )
        cat_alimentacao, _ = CategoriaFinanceira.objects.get_or_create(
            nome="Alimentacao", tipo=CategoriaFinanceira.DESPESA
        )

        LancamentoFinanceiro.objects.get_or_create(
            evento=evento,
            tipo=LancamentoFinanceiro.RECEITA,
            categoria=cat_inscricao,
            conta=conta,
            data=date.today(),
            descricao="Receita ficticia - inscricoes",
            valor=Decimal("1200.00"),
            forma_pagamento=LancamentoFinanceiro.PIX,
            criado_por=admin_user,
            atualizado_por=admin_user,
        )
        LancamentoFinanceiro.objects.get_or_create(
            evento=evento,
            tipo=LancamentoFinanceiro.DESPESA,
            categoria=cat_alimentacao,
            conta=conta,
            data=date.today(),
            descricao="Despesa ficticia - alimentacao",
            valor=Decimal("450.00"),
            forma_pagamento=LancamentoFinanceiro.DINHEIRO,
            criado_por=admin_user,
            atualizado_por=admin_user,
        )

        arroz, _ = Produto.objects.get_or_create(
            sku="EST-ARROZ-001",
            defaults={
                "nome": "Arroz 5kg",
                "unidade": "UN",
                "estoque_minimo": Decimal("5.00"),
                "estoque_maximo": Decimal("30.00"),
                "estoque_atual": Decimal("12.00"),
            },
        )
        agua, _ = Produto.objects.get_or_create(
            sku="EST-AGUA-001",
            defaults={
                "nome": "Agua mineral 500ml",
                "unidade": "UN",
                "estoque_minimo": Decimal("50.00"),
                "estoque_maximo": Decimal("300.00"),
                "estoque_atual": Decimal("180.00"),
            },
        )

        MovimentoEstoque.objects.get_or_create(
            tipo=MovimentoEstoque.SAIDA,
            evento=evento,
            produto=arroz,
            data=date.today(),
            quantidade=Decimal("2.00"),
            observacao="Uso na cozinha do ciclo",
            criado_por=admin_user,
        )

        chale, _ = Chale.objects.get_or_create(
            codigo="A1",
            defaults={
                "capacidade": 6,
                "status": Chale.ATIVO,
                "acessivel_cadeirante": True,
            },
        )

        ReservaChale.objects.get_or_create(
            evento=evento,
            chale=chale,
            defaults={
                "responsavel_nome": "Hospede Exemplo",
                "qtd_pessoas": 4,
                "status": ReservaChale.CONFIRMADA,
                "valor_adicional": Decimal("150.00"),
                "pago": True,
                "forma_pagamento": LancamentoFinanceiro.PIX,
                "conta": conta,
                "criado_por": admin_user,
                "atualizado_por": admin_user,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed Eventa aplicada com sucesso."))

    def _seed_groups(self):
        for group_name in [
            ROLE_ADMIN,
            ROLE_FINANCEIRO,
            ROLE_FINANCEIRO_LEITURA,
            ROLE_ESTOQUE,
            ROLE_ESTOQUE_LEITURA,
            ROLE_HOSPEDAGEM,
            ROLE_HOSPEDAGEM_LEITURA,
            ROLE_MENSAGENS,
            ROLE_MENSAGENS_LEITURA,
            ROLE_COORDENADOR,
            ROLE_VISUALIZACAO,
        ]:
            Group.objects.get_or_create(name=group_name)

    def _seed_users(self):
        admin_user, created = User.objects.get_or_create(
            username="eventa_admin",
            defaults={"email": "admin@eventa.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("eventa123")
            admin_user.save()

        Group.objects.get(name=ROLE_ADMIN).user_set.add(admin_user)

        financeiro_user, created = User.objects.get_or_create(
            username="eventa_financeiro",
            defaults={"email": "financeiro@eventa.local", "is_staff": False, "is_superuser": False},
        )
        if created:
            financeiro_user.set_password("eventa123")
            financeiro_user.save()
        Group.objects.get(name=ROLE_FINANCEIRO).user_set.add(financeiro_user)

        return admin_user
