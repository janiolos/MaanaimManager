from datetime import date
from decimal import Decimal
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.core.models import Evento


class Produto(models.Model):
    CATEGORIA_MATERIA_PRIMA = "MATERIA_PRIMA"
    CATEGORIA_PRODUTO_ACABADO = "PRODUTO_ACABADO"
    CATEGORIA_COMPONENTE = "COMPONENTE"
    CATEGORIA_CHOICES = [
        (CATEGORIA_MATERIA_PRIMA, "Materia-Prima"),
        (CATEGORIA_PRODUTO_ACABADO, "Produto Acabado"),
        (CATEGORIA_COMPONENTE, "Componente"),
    ]

    nome = models.CharField(max_length=140)
    sku = models.CharField(max_length=40, unique=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default=CATEGORIA_MATERIA_PRIMA)
    unidade = models.CharField(max_length=20, default="UN")
    estoque_atual = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estoque_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estoque_reabastecimento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estoque_maximo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    valor_estoque_atual = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    custo_medio_atual = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.0000"))
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.sku})"

    @property
    def status_estoque(self):
        if self.estoque_atual < self.estoque_minimo:
            return "BAIXO"
        if self.precisa_reabastecimento:
            return "REABASTECER"
        if self.estoque_maximo > 0 and self.estoque_atual > self.estoque_maximo:
            return "ACIMA"
        return "OK"

    @property
    def precisa_reabastecimento(self):
        return self.estoque_reabastecimento > 0 and self.estoque_atual < self.estoque_reabastecimento

    def registrar_entrada(self, quantidade, custo_unitario):
        quantidade = Decimal(quantidade)
        custo_unitario = Decimal(custo_unitario)
        if quantidade <= 0:
            raise ValidationError({"quantidade": "A quantidade deve ser maior que zero."})
        if custo_unitario < 0:
            raise ValidationError({"custo_unitario": "O custo unitario nao pode ser negativo."})

        novo_estoque = self.estoque_atual + quantidade
        novo_valor = self.valor_estoque_atual + (quantidade * custo_unitario)
        novo_custo_medio = Decimal("0.0000")
        if novo_estoque > 0:
            novo_custo_medio = novo_valor / novo_estoque

        self.estoque_atual = novo_estoque
        self.valor_estoque_atual = novo_valor
        self.custo_medio_atual = novo_custo_medio

    def aplicar_saida(self, quantidade):
        quantidade = Decimal(quantidade)
        if quantidade <= 0:
            raise ValidationError({"quantidade": "A quantidade deve ser maior que zero."})
        if self.estoque_atual < quantidade:
            raise ValidationError(
                {"quantidade": f"Estoque insuficiente para {self.nome}. Disponivel: {self.estoque_atual}."}
            )

        custo_total_saida = quantidade * self.custo_medio_atual
        self.estoque_atual -= quantidade
        self.valor_estoque_atual -= custo_total_saida

        if self.estoque_atual > 0:
            self.custo_medio_atual = self.valor_estoque_atual / self.estoque_atual
        else:
            self.valor_estoque_atual = Decimal("0.0000")
            self.custo_medio_atual = Decimal("0.0000")

        return custo_total_saida


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

    @property
    def valor_total(self):
        return self.quantidade * self.custo_unitario


class MovimentoEstoque(models.Model):
    """Modelo legado. Mantido apenas para historico e compatibilidade."""

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


class RequisicaoSaida(models.Model):
    ABERTA = "ABERTA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = [
        (ABERTA, "Aberta"),
        (FINALIZADA, "Finalizada"),
        (CANCELADA, "Cancelada"),
    ]
    AREAS_CHOICES = [
        ("COZINHA", "Cozinha"),
        ("COPA", "Copa"),
        ("CANTINA", "Cantina"),
        ("COPA_PASTORES", "Copa Pastores"),
        ("SECRETARIA", "Secretaria"),
    ]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name="requisicoes_saida")
    area = models.CharField(max_length=80, choices=AREAS_CHOICES)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ABERTA)
    observacao = models.CharField(max_length=255, blank=True)
    protocolo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    finalizado_em = models.DateTimeField(null=True, blank=True)
    finalizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="requisicoes_finalizadas",
    )
    impresso_em = models.DateTimeField(null=True, blank=True)
    impresso_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="requisicoes_impressas",
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requisicoes_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.numero or f"Requisicao {self.pk}"

    @property
    def pode_editar(self):
        return self.status == self.ABERTA

    @property
    def total_itens(self):
        return self.itens.count()

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.numero:
            ano = self.data_solicitacao.year if self.data_solicitacao else date.today().year
            self.numero = f"REQ-{ano}-{self.pk:06d}"
            self.__class__.objects.filter(pk=self.pk).update(numero=self.numero)

    def finalizar(self, user):
        if self.status != self.ABERTA:
            raise ValidationError("Somente requisicoes em aberto podem ser finalizadas.")

        with transaction.atomic():
            requisicao = (
                RequisicaoSaida.objects.select_for_update()
                .prefetch_related("itens__produto")
                .get(pk=self.pk)
            )
            itens = list(requisicao.itens.all())
            if not itens:
                raise ValidationError("A requisicao precisa ter ao menos um item.")

            produtos_por_id = {
                p.pk: p
                for p in Produto.objects.select_for_update()
                .filter(pk__in=[item.produto_id for item in itens])
                .order_by("pk")
            }

            for item in itens:
                produto = produtos_por_id[item.produto_id]
                if produto.estoque_atual < item.quantidade:
                    raise ValidationError(
                        f"Estoque insuficiente para {produto.nome}. Disponivel: {produto.estoque_atual}."
                    )

            for item in itens:
                produto = produtos_por_id[item.produto_id]
                saldo_antes = produto.estoque_atual
                custo_medio = produto.custo_medio_atual
                custo_total = produto.aplicar_saida(item.quantidade)
                produto.save(update_fields=["estoque_atual", "valor_estoque_atual", "custo_medio_atual"])

                item.saldo_antes = saldo_antes
                item.saldo_depois = produto.estoque_atual
                item.custo_medio_unitario = custo_medio
                item.custo_total = custo_total
                item.save(
                    update_fields=[
                        "saldo_antes",
                        "saldo_depois",
                        "custo_medio_unitario",
                        "custo_total",
                    ]
                )

            from django.utils import timezone

            requisicao.status = self.FINALIZADA
            requisicao.finalizado_em = timezone.now()
            requisicao.finalizado_por = user
            requisicao.save(update_fields=["status", "finalizado_em", "finalizado_por"])


class RequisicaoSaidaItem(models.Model):
    requisicao = models.ForeignKey(RequisicaoSaida, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)
    custo_medio_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.0000"))
    custo_total = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    saldo_antes = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    saldo_depois = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("requisicao", "produto")]
        ordering = ["id"]

    def __str__(self):
        return f"{self.produto} x {self.quantidade}"

    def clean(self):
        super().clean()
        if self.quantidade <= 0:
            raise ValidationError({"quantidade": "A quantidade deve ser maior que zero."})


class RequisicaoSaidaImpressao(models.Model):
    ORIGINAL = "ORIGINAL"
    SEGUNDA_VIA = "2A_VIA"
    VIA_CHOICES = [(ORIGINAL, "Original"), (SEGUNDA_VIA, "2a via")]

    requisicao = models.ForeignKey(RequisicaoSaida, on_delete=models.CASCADE, related_name="impressoes")
    impresso_em = models.DateTimeField(auto_now_add=True)
    impresso_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    via = models.CharField(max_length=20, choices=VIA_CHOICES, default=ORIGINAL)

    class Meta:
        ordering = ["-impresso_em"]

    def __str__(self):
        return f"{self.requisicao.numero} - {self.get_via_display()}"


class Fornecedor(models.Model):
    nome = models.CharField(max_length=140, unique=True)
    documento = models.CharField(max_length=30, blank=True)
    contato = models.CharField(max_length=120, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class CotacaoCompra(models.Model):
    ABERTA = "ABERTA"
    FECHADA = "FECHADA"
    CANCELADA = "CANCELADA"
    STATUS_CHOICES = [
        (ABERTA, "Aberta"),
        (FECHADA, "Fechada"),
        (CANCELADA, "Cancelada"),
    ]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name="cotacoes_compra")
    data_cotacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ABERTA)
    observacao = models.CharField(max_length=255, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cotacoes_criadas")
    fornecedor_aprovado = models.ForeignKey(
        "inventory.Fornecedor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cotacoes_aprovadas",
    )
    valor_aprovado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    aprovado_em = models.DateTimeField(null=True, blank=True)
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cotacoes_aprovadas_por",
    )
    lancamento_financeiro = models.ForeignKey(
        "finance.LancamentoFinanceiro",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cotacoes_origem",
    )
    fechado_em = models.DateTimeField(null=True, blank=True)
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cotacoes_fechadas",
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.numero or f"Cotacao {self.pk}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.numero:
            ano = self.data_cotacao.year if self.data_cotacao else date.today().year
            self.numero = f"COT-{ano}-{self.pk:06d}"
            self.__class__.objects.filter(pk=self.pk).update(numero=self.numero)

    @property
    def total_itens(self):
        return self.itens.count()

    def totais_por_fornecedor(self):
        totais = {}
        for preco in self.precos.select_related("fornecedor").all():
            fornecedor_id = preco.fornecedor_id
            registro = totais.setdefault(
                fornecedor_id,
                {"fornecedor": preco.fornecedor, "total": Decimal("0.00")},
            )
            registro["total"] += preco.valor_total
        return totais

    def melhor_proposta_total(self):
        totais = [r["total"] for r in self.totais_por_fornecedor().values() if r["total"] > 0]
        if not totais:
            return None
        return min(totais)

    @property
    def melhor_total(self):
        return self.melhor_proposta_total()

    @property
    def tem_ordem_compra(self):
        try:
            return bool(self.ordem_compra)
        except Exception:
            return False

    @property
    def numero_ordem_compra(self):
        try:
            return self.ordem_compra.numero
        except Exception:
            return ""

    def fechar(self, user):
        if self.status != self.ABERTA:
            raise ValidationError("Somente cotacoes em aberto podem ser fechadas.")
        if not self.itens.exists():
            raise ValidationError("A cotacao precisa ter ao menos um item.")
        if not self.precos.exists():
            raise ValidationError("Informe ao menos um preco para fechar a cotacao.")

        from django.utils import timezone

        self.status = self.FECHADA
        self.fechado_em = timezone.now()
        self.fechado_por = user
        self.save(update_fields=["status", "fechado_em", "fechado_por"])


class OrdemCompra(models.Model):
    PENDENTE = "PENDENTE"
    ENVIADA = "ENVIADA"
    FALHA = "FALHA"
    STATUS_ENVIO_CHOICES = [
        (PENDENTE, "Pendente"),
        (ENVIADA, "Enviada"),
        (FALHA, "Falha"),
    ]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    cotacao = models.OneToOneField(CotacaoCompra, on_delete=models.PROTECT, related_name="ordem_compra")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name="ordens_compra")
    mensagem = models.TextField()
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    status_envio = models.CharField(max_length=12, choices=STATUS_ENVIO_CHOICES, default=PENDENTE)
    twilio_sid = models.CharField(max_length=100, blank=True)
    erro_envio = models.CharField(max_length=255, blank=True)
    enviada_em = models.DateTimeField(null=True, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ordens_compra_criadas")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.numero or f"OC {self.pk}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.numero:
            ano = self.criado_em.year if self.criado_em else date.today().year
            self.numero = f"OC-{ano}-{self.pk:06d}"
            self.__class__.objects.filter(pk=self.pk).update(numero=self.numero)


class CotacaoCompraItem(models.Model):
    cotacao = models.ForeignKey(CotacaoCompra, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        unique_together = [("cotacao", "produto")]

    def __str__(self):
        return f"{self.produto} x {self.quantidade}"

    def clean(self):
        super().clean()
        if self.quantidade <= 0:
            raise ValidationError({"quantidade": "A quantidade deve ser maior que zero."})


class CotacaoCompraPreco(models.Model):
    cotacao = models.ForeignKey(CotacaoCompra, on_delete=models.CASCADE, related_name="precos")
    item = models.ForeignKey(CotacaoCompraItem, on_delete=models.CASCADE, related_name="precos")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("item", "fornecedor")]
        ordering = ["fornecedor__nome", "item__id"]

    def __str__(self):
        return f"{self.item} - {self.fornecedor}: {self.valor_unitario}"

    def clean(self):
        super().clean()
        if self.valor_unitario < 0:
            raise ValidationError({"valor_unitario": "O valor unitario nao pode ser negativo."})

    def save(self, *args, **kwargs):
        self.valor_total = self.item.quantidade * self.valor_unitario
        super().save(*args, **kwargs)


class CotacaoCompraImpressao(models.Model):
    ORIGINAL = "ORIGINAL"
    SEGUNDA_VIA = "2A_VIA"
    VIA_CHOICES = [(ORIGINAL, "Original"), (SEGUNDA_VIA, "2a via")]

    cotacao = models.ForeignKey(CotacaoCompra, on_delete=models.CASCADE, related_name="impressoes")
    impresso_em = models.DateTimeField(auto_now_add=True)
    impresso_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    via = models.CharField(max_length=20, choices=VIA_CHOICES, default=ORIGINAL)

    class Meta:
        ordering = ["-impresso_em"]

    def __str__(self):
        return f"{self.cotacao.numero} - {self.get_via_display()}"
