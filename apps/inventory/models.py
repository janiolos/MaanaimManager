from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import Evento


class Produto(models.Model):
    nome = models.CharField(max_length=140)
    sku = models.CharField(max_length=40, unique=True)
    unidade = models.CharField(max_length=20, default="UN")
    estoque_atual = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estoque_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estoque_maximo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.sku})"

    @property
    def status_estoque(self):
        if self.estoque_atual < self.estoque_minimo:
            return "BAIXO"
        if self.estoque_maximo > 0 and self.estoque_atual > self.estoque_maximo:
            return "ACIMA"
        return "OK"


class EntradaEstoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    data = models.DateField()
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    documento = models.CharField(max_length=120, blank=True)
    observacao = models.CharField(max_length=255, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"Entrada {self.produto} ({self.quantidade})"


class MovimentoEstoque(models.Model):
    SAIDA = "SAIDA"
    DEVOLUCAO = "DEVOLUCAO"
    TIPOS = [(SAIDA, "Saida"), (DEVOLUCAO, "Devolucao")]

    tipo = models.CharField(max_length=12, choices=TIPOS)
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    data = models.DateField()
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)
    observacao = models.CharField(max_length=255, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.produto} ({self.quantidade})"

    def clean(self):
        super().clean()
        if self.quantidade <= 0:
            raise ValidationError({"quantidade": "A quantidade deve ser maior que zero."})

