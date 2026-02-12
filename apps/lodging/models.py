from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import Evento
from apps.finance.models import LancamentoFinanceiro


class Chale(models.Model):
    ATIVO = "ATIVO"
    MANUTENCAO = "MANUTENCAO"
    INATIVO = "INATIVO"
    STATUS_CHOICES = [
        (ATIVO, "Ativo"),
        (MANUTENCAO, "Manutencao"),
        (INATIVO, "Inativo"),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    capacidade = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ATIVO)
    acessivel_cadeirante = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Chale"
        verbose_name_plural = "Chales"
        ordering = ["codigo"]

    def __str__(self):
        return self.codigo


class ReservaChale(models.Model):
    PRE_RESERVA = "PRE_RESERVA"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = [
        (PRE_RESERVA, "Pre-reserva"),
        (CONFIRMADA, "Confirmada"),
        (CANCELADA, "Cancelada"),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.PROTECT)
    chale = models.ForeignKey(Chale, on_delete=models.PROTECT)
    responsavel_nome = models.CharField(max_length=120)
    qtd_pessoas = models.PositiveIntegerField()
    qtd_criancas = models.PositiveIntegerField(default=0)
    idades_criancas = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PRE_RESERVA)
    valor_adicional = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pago = models.BooleanField(default=False)
    forma_pagamento = models.CharField(
        max_length=10,
        choices=LancamentoFinanceiro.FORMAS_PAGAMENTO,
        blank=True,
    )
    conta = models.ForeignKey(
        "finance.ContaCaixa",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    lancamento_financeiro = models.ForeignKey(
        "finance.LancamentoFinanceiro",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reservas_chale",
    )
    observacoes = models.TextField(blank=True)

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservas_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservas_atualizadas",
        null=True,
        blank=True,
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reserva de chale"
        verbose_name_plural = "Reservas de chale"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "chale"],
                name="unique_chale_por_evento",
            )
        ]

    def __str__(self):
        return f"{self.evento} - {self.chale}"

    def clean(self):
        chale = self.chale if self.chale_id else None
        total_hospedes = (self.qtd_pessoas or 0) + (self.qtd_criancas or 0)
        if total_hospedes and chale and total_hospedes > chale.capacidade:
            raise ValidationError({"qtd_pessoas": "Total de hospedes excede a capacidade do chale."})
        if chale and chale.status != Chale.ATIVO:
            raise ValidationError({"chale": "Chale indisponivel para reserva."})
        if self.evento_id and self.chale_id:
            conflito = (
                ReservaChale.objects.filter(evento_id=self.evento_id, chale_id=self.chale_id)
                .exclude(pk=self.pk)
                .exists()
            )
            if conflito:
                raise ValidationError({"chale": "Chale ja reservado neste evento."})
