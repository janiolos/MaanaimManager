from django.conf import settings
from django.db import models

from apps.core.models import Evento


class CategoriaFinanceira(models.Model):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    TIPOS = [(RECEITA, "Receita"), (DESPESA, "Despesa")]

    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPOS)

    class Meta:
        verbose_name = "Categoria financeira"
        verbose_name_plural = "Categorias financeiras"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class ContaCaixa(models.Model):
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Conta de caixa"
        verbose_name_plural = "Contas de caixa"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class LancamentoFinanceiro(models.Model):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    TIPOS = [(RECEITA, "Receita"), (DESPESA, "Despesa")]

    DINHEIRO = "DINHEIRO"
    PIX = "PIX"
    CARTAO = "CARTAO"
    OUTRO = "OUTRO"
    FORMAS_PAGAMENTO = [
        (DINHEIRO, "Dinheiro"),
        (PIX, "PIX"),
        (CARTAO, "Cartao"),
        (OUTRO, "Outro"),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    categoria = models.ForeignKey(CategoriaFinanceira, on_delete=models.PROTECT)
    conta = models.ForeignKey(ContaCaixa, on_delete=models.PROTECT)
    data = models.DateField()
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField(max_length=10, choices=FORMAS_PAGAMENTO)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lancamentos_criados"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lancamentos_atualizados",
        null=True,
        blank=True,
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lancamento financeiro"
        verbose_name_plural = "Lancamentos financeiros"
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"{self.descricao} - {self.valor}"


class AnexoLancamento(models.Model):
    lancamento = models.ForeignKey(LancamentoFinanceiro, on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to="anexos/")
    descricao = models.CharField(max_length=255, blank=True)
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo de lancamento"
        verbose_name_plural = "Anexos de lancamento"
        ordering = ["-enviado_em"]

    def __str__(self):
        return self.descricao or self.arquivo.name
