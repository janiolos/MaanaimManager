from django.db import models
from django.conf import settings
from apps.core.models import Evento
from apps.inventory.models import Produto

class VendaMobile(models.Model):
    id_referencia = models.CharField(max_length=50, unique=True, help_text="Timestamp ou ID gerado no frontend")
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name='vendas_mobile')
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vendas_mobile')
    data_hora = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['-data_hora']
        verbose_name = "Venda Mobile"
        verbose_name_plural = "Vendas Mobile"
        
    def __str__(self):
        return f"Venda {self.id_referencia} - R$ {self.total}"

class ItemVendaMobile(models.Model):
    venda = models.ForeignKey(VendaMobile, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total_item = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = "Item da Venda Mobile"
        verbose_name_plural = "Itens da Venda Mobile"

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Venda {self.venda.id_referencia})"
