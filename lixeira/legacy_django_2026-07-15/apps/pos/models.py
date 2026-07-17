from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.core.models import Evento
from apps.inventory.models import Produto


# ---------------------------------------------------------------------------
# ESTRUTURA DO PDV POR EVENTO
# ---------------------------------------------------------------------------

class LocalVenda(models.Model):
    """
    Um ponto de venda físico dentro de um Evento.
    Ex: Fazendinha, Cantina, Secretaria, Livraria.
    Cada evento monta seus próprios locais.
    """
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='locais_venda',
        verbose_name='Evento',
    )
    nome = models.CharField(max_length=120, verbose_name='Nome do local')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    # Permissões de módulos visíveis neste local
    modulo_dashboard = models.BooleanField(default=True, verbose_name='Dashboard')
    modulo_pdv = models.BooleanField(default=True, verbose_name='PDV (Caixa)')
    modulo_vendas = models.BooleanField(default=True, verbose_name='Vendas')
    modulo_produtos = models.BooleanField(default=False, verbose_name='Produtos')
    modulo_estoque = models.BooleanField(default=True, verbose_name='Estoque')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Local de Venda'
        verbose_name_plural = 'Locais de Venda'
        ordering = ['evento', 'nome']
        unique_together = [('evento', 'nome')]

    def __str__(self):
        return f'{self.nome} ({self.evento})'


class FamiliaVenda(models.Model):
    """
    Agrupamento de produtos dentro de um local de venda.
    Ex: Bebidas, Lanches, Salgados — cada local tem suas próprias famílias.
    """
    local = models.ForeignKey(
        LocalVenda,
        on_delete=models.CASCADE,
        related_name='familias',
        verbose_name='Local de venda',
    )
    nome = models.CharField(max_length=120, verbose_name='Nome da família')

    class Meta:
        verbose_name = 'Família de Produtos (PDV)'
        verbose_name_plural = 'Famílias de Produtos (PDV)'
        ordering = ['local', 'nome']
        unique_together = [('local', 'nome')]

    def __str__(self):
        return f'{self.nome} — {self.local.nome}'


class ProdutoLocal(models.Model):
    """
    Sub-estoque de um produto em um local de venda específico.
    Cada local tem seu próprio preço de venda e controle de estoque
    independentes do estoque global em apps.inventory.
    """
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='locais',
        verbose_name='Produto (catálogo)',
    )
    local = models.ForeignKey(
        LocalVenda,
        on_delete=models.CASCADE,
        related_name='produtos',
        verbose_name='Local de venda',
    )
    familia = models.ForeignKey(
        FamiliaVenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Família',
    )

    # Preço e estoque independentes por local
    preco_venda = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Preço de venda (R$)',
    )
    estoque_atual = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Estoque atual',
    )
    estoque_minimo = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Estoque mínimo (EM)',
    )
    ponto_reabastecimento = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Ponto de reabastecimento (PR)',
    )
    estoque_maximo = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Estoque máximo (EMáx)',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo no local')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Produto no Local (Sub-estoque)'
        verbose_name_plural = 'Produtos nos Locais (Sub-estoque)'
        ordering = ['local', 'familia', 'produto']
        unique_together = [('produto', 'local')]

    def __str__(self):
        return f'{self.produto.nome} @ {self.local.nome}'

    @property
    def status_estoque(self):
        if self.estoque_atual < self.estoque_minimo:
            return 'BAIXO'
        if self.ponto_reabastecimento > 0 and self.estoque_atual < self.ponto_reabastecimento:
            return 'REABASTECER'
        return 'OK'

    def aplicar_saida(self, quantidade):
        """Diminui o sub-estoque local. Lança ValueError se insuficiente."""
        from django.core.exceptions import ValidationError
        quantidade = Decimal(str(quantidade))
        if self.estoque_atual < quantidade:
            raise ValidationError(
                f'Estoque insuficiente para {self.produto.nome} em {self.local.nome}. '
                f'Disponível: {self.estoque_atual}.'
            )
        self.estoque_atual -= quantidade


class EntradaEstoqueLocal(models.Model):
    """
    Registro de entrada de mercadoria em um local de venda específico.
    Atualiza o sub-estoque (ProdutoLocal.estoque_atual) e o preço de venda.
    """
    produto_local = models.ForeignKey(
        ProdutoLocal,
        on_delete=models.CASCADE,
        related_name='entradas',
        verbose_name='Produto no local',
    )
    quantidade = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Quantidade entrada',
    )
    preco_custo = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Preço de custo (R$)',
    )
    preco_venda = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Preço de venda (R$)',
    )
    data = models.DateField(verbose_name='Data da entrada')
    observacao = models.CharField(max_length=255, blank=True, verbose_name='Observação')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='entradas_estoque_local',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrada de Estoque (Local PDV)'
        verbose_name_plural = 'Entradas de Estoque (Local PDV)'
        ordering = ['-criado_em']

    def __str__(self):
        return f'+{self.quantidade} {self.produto_local.produto.nome} → {self.produto_local.local.nome}'


# ---------------------------------------------------------------------------
# VENDAS DO PDV
# ---------------------------------------------------------------------------

class VendaMobile(models.Model):
    """Venda realizada pelo PDV em um evento/local."""

    id_referencia = models.CharField(
        max_length=50, unique=True,
        help_text='Timestamp ou UUID gerado no frontend',
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name='vendas_pdv',
        verbose_name='Evento',
    )
    local = models.ForeignKey(
        LocalVenda,
        on_delete=models.PROTECT,
        related_name='vendas',
        verbose_name='Local de venda',
        null=True, blank=True,
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vendas_pdv',
    )
    data_hora = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total (R$)')
    # forma_pagamento mantida por compatibilidade; pagamentos detalhados em PagamentoVenda
    forma_pagamento = models.CharField(max_length=20, default='MISTO', blank=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Venda PDV'
        verbose_name_plural = 'Vendas PDV'

    def __str__(self):
        return f'Venda {self.id_referencia} — R$ {self.total}'


class PagamentoVenda(models.Model):
    """Detalhe de pagamento de uma venda (suporte a pagamento misto)."""

    DINHEIRO = 'DINHEIRO'
    PIX = 'PIX'
    DEBITO = 'DÉBITO'
    CREDITO = 'CRÉDITO'
    TIPOS = [
        (DINHEIRO, 'Dinheiro'),
        (PIX, 'PIX'),
        (DEBITO, 'Débito'),
        (CREDITO, 'Crédito'),
    ]

    venda = models.ForeignKey(
        VendaMobile,
        on_delete=models.CASCADE,
        related_name='pagamentos',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Pagamento da Venda'
        verbose_name_plural = 'Pagamentos das Vendas'

    def __str__(self):
        return f'{self.get_tipo_display()}: R$ {self.valor}'


class ItemVendaMobile(models.Model):
    """Item de uma venda: referencia o sub-estoque (ProdutoLocal)."""

    venda = models.ForeignKey(
        VendaMobile,
        on_delete=models.CASCADE,
        related_name='itens',
    )
    produto_local = models.ForeignKey(
        ProdutoLocal,
        on_delete=models.PROTECT,
        related_name='itens_venda',
        verbose_name='Produto no local',
        null=True, blank=True,
    )
    # Snapshot do nome/código para histórico (caso o produto seja desativado)
    nome_produto = models.CharField(max_length=140, blank=True)
    codigo_produto = models.CharField(max_length=40, blank=True)
    familia_produto = models.CharField(max_length=120, blank=True)

    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    desconto_perc = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Desconto (%)',
    )
    total_item = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Item da Venda PDV'
        verbose_name_plural = 'Itens das Vendas PDV'

    def __str__(self):
        return f'{self.quantidade}x {self.nome_produto} (Venda {self.venda.id_referencia})'


# ---------------------------------------------------------------------------
# SIGNALS
# ---------------------------------------------------------------------------

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Evento)
def criar_locais_venda_padrao(sender, instance, created, **kwargs):
    if created:
        locais_padrao = [
            "Fazendinha",
            "Cantina",
            "Secretaria",
            "Livraria",
        ]
        for nome_local in locais_padrao:
            LocalVenda.objects.get_or_create(
                evento=instance,
                nome=nome_local,
                defaults={
                    'modulo_dashboard': True,
                    'modulo_pdv': True,
                    'modulo_vendas': True,
                    'modulo_produtos': False,
                    'modulo_estoque': True,
                }
            )

