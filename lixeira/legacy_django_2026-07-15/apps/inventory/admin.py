from django.contrib import admin

from .models import (
    CotacaoCompra,
    CotacaoCompraImpressao,
    CotacaoCompraItem,
    CotacaoCompraPreco,
    EntradaEstoque,
    Fornecedor,
    MovimentoEstoque,
    OrdemCompra,
    Produto,
    RequisicaoSaida,
    RequisicaoSaidaImpressao,
    RequisicaoSaidaItem,
)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "sku",
        "categoria",
        "unidade",
        "estoque_atual",
        "custo_medio_atual",
        "valor_estoque_atual",
        "estoque_minimo",
        "estoque_reabastecimento",
        "estoque_maximo",
        "ativo",
    )
    list_filter = ("ativo", "categoria")
    search_fields = ("nome", "sku")


@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "data", "quantidade", "custo_unitario", "documento", "criado_por")
    list_filter = ("data",)
    search_fields = ("produto__nome", "documento")


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("tipo", "evento", "produto", "data", "quantidade", "criado_por")
    list_filter = ("tipo", "data", "evento")
    search_fields = ("produto__nome", "evento__nome")


class RequisicaoSaidaItemInline(admin.TabularInline):
    model = RequisicaoSaidaItem
    extra = 0


@admin.register(RequisicaoSaida)
class RequisicaoSaidaAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "evento",
        "area",
        "status",
        "data_solicitacao",
        "criado_por",
        "finalizado_em",
    )
    list_filter = ("status", "evento", "area")
    search_fields = ("numero", "area", "evento__nome")
    inlines = [RequisicaoSaidaItemInline]


@admin.register(RequisicaoSaidaImpressao)
class RequisicaoSaidaImpressaoAdmin(admin.ModelAdmin):
    list_display = ("requisicao", "via", "impresso_em", "impresso_por")
    list_filter = ("via", "impresso_em")
    search_fields = ("requisicao__numero",)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "contato", "telefone", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "documento", "contato", "email")


class CotacaoCompraPrecoInline(admin.TabularInline):
    model = CotacaoCompraPreco
    extra = 0


class CotacaoCompraItemInline(admin.TabularInline):
    model = CotacaoCompraItem
    extra = 0


@admin.register(CotacaoCompra)
class CotacaoCompraAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "evento",
        "status",
        "fornecedor_aprovado",
        "valor_aprovado",
        "data_cotacao",
        "criado_por",
        "fechado_em",
    )
    list_filter = ("status", "evento")
    search_fields = ("numero", "evento__nome")
    inlines = [CotacaoCompraItemInline, CotacaoCompraPrecoInline]


@admin.register(CotacaoCompraImpressao)
class CotacaoCompraImpressaoAdmin(admin.ModelAdmin):
    list_display = ("cotacao", "via", "impresso_em", "impresso_por")
    list_filter = ("via", "impresso_em")
    search_fields = ("cotacao__numero",)


@admin.register(OrdemCompra)
class OrdemCompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "cotacao", "fornecedor", "valor_total", "status_envio", "enviada_em")
    list_filter = ("status_envio", "enviada_em")
    search_fields = ("numero", "cotacao__numero", "fornecedor__nome", "twilio_sid")
