from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro
from apps.core.models import Evento
from datetime import date
from decimal import Decimal

User = get_user_model()

class FinanceSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="123")
        self.evento = Evento.objects.create(
            nome="Evento Teste",
            data_inicio="2030-01-01T00:00:00Z",
            data_fim="2030-01-02T00:00:00Z",
            status=Evento.EM_ANDAMENTO,
        )
        self.categoria = CategoriaFinanceira.objects.create(
            nome="Doacao",
            tipo=CategoriaFinanceira.RECEITA
        )
        self.conta = ContaCaixa.objects.create(nome="Caixa Principal")

    def test_lancamento_financeiro_creation(self):
        lancamento = LancamentoFinanceiro.objects.create(
            evento=self.evento,
            tipo=LancamentoFinanceiro.RECEITA,
            categoria=self.categoria,
            conta=self.conta,
            data=date(2030, 1, 1),
            descricao="Oferta teste",
            valor=Decimal("150.00"),
            forma_pagamento=LancamentoFinanceiro.DINHEIRO,
            criado_por=self.user,
        )
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        self.assertEqual(lancamento.valor, Decimal("150.00"))
