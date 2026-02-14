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
    data_entrada = models.DateField(null=True, blank=True)
    data_saida = models.DateField(null=True, blank=True)
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

    def __str__(self):
        return f"{self.evento} - {self.chale}"

    def clean(self):
        chale = self.chale if self.chale_id else None
        total_hospedes = (self.qtd_pessoas or 0) + (self.qtd_criancas or 0)
        data_entrada = self.data_entrada
        data_saida = self.data_saida

        if not data_entrada or not data_saida:
            raise ValidationError({"data_entrada": "Informe periodo da reserva."})
        if data_saida <= data_entrada:
            raise ValidationError({"data_saida": "A data de saida deve ser maior que a de entrada."})

        if total_hospedes and chale and total_hospedes > chale.capacidade:
            raise ValidationError({"qtd_pessoas": "Total de hospedes excede a capacidade do chale."})
        if chale and chale.status != Chale.ATIVO:
            raise ValidationError({"chale": "Chale indisponivel para reserva."})
        if self.evento_id and self.chale_id:
            conflito = ReservaChale.objects.filter(
                evento_id=self.evento_id,
                chale_id=self.chale_id,
                status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
                data_entrada__lt=data_saida,
                data_saida__gt=data_entrada,
            ).exclude(pk=self.pk).exists()
            if conflito:
                raise ValidationError({"chale": "Chale ja reservado para este periodo."})

            if AcaoChale.objects.filter(
                evento_id=self.evento_id,
                chale_id=self.chale_id,
                ativo=True,
                data_inicio__lt=data_saida,
                data_fim__gt=data_entrada,
            ).exists():
                raise ValidationError({"chale": "Existe bloqueio/manutencao para este periodo."})


class AcaoChale(models.Model):
    BLOQUEIO = "BLOQUEIO"
    MANUTENCAO = "MANUTENCAO"
    TIPO_CHOICES = [
        (BLOQUEIO, "Bloqueio"),
        (MANUTENCAO, "Manutencao"),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.PROTECT)
    chale = models.ForeignKey(Chale, on_delete=models.PROTECT, related_name="acoes_periodo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=120)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acoes_chale_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="acoes_chale_atualizadas",
        null=True,
        blank=True,
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Acao de chale"
        verbose_name_plural = "Acoes de chale"
        ordering = ["-data_inicio", "-id"]

    def __str__(self):
        return f"{self.chale.codigo} - {self.get_tipo_display()} ({self.data_inicio} a {self.data_fim})"

    def clean(self):
        if self.data_fim <= self.data_inicio:
            raise ValidationError({"data_fim": "Data final deve ser maior que data inicial."})

        if self.evento_id and self.chale_id:
            conflito_reserva = ReservaChale.objects.filter(
                evento_id=self.evento_id,
                chale_id=self.chale_id,
                status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
                data_entrada__lt=self.data_fim,
                data_saida__gt=self.data_inicio,
            ).exists()
            if conflito_reserva:
                raise ValidationError({"data_inicio": "Existe reserva ativa no periodo informado."})

            conflito_acao = AcaoChale.objects.filter(
                evento_id=self.evento_id,
                chale_id=self.chale_id,
                ativo=True,
                data_inicio__lt=self.data_fim,
                data_fim__gt=self.data_inicio,
            ).exclude(pk=self.pk).exists()
            if conflito_acao:
                raise ValidationError({"data_inicio": "Ja existe bloqueio/manutencao no periodo informado."})
