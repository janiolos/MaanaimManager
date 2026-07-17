from django.contrib import admin
from .models import (
    LocalVenda, FamiliaVenda, ProdutoLocal, EntradaEstoqueLocal,
    VendaMobile, PagamentoVenda, ItemVendaMobile,
)


# ---------------------------------------------------------------------------
# INLINES
# ---------------------------------------------------------------------------

class FamiliaVendaInline(admin.TabularInline):
    model = FamiliaVenda
    extra = 1
    fields = ('nome',)


class ProdutoLocalInline(admin.TabularInline):
    model = ProdutoLocal
    extra = 0
    fields = ('produto', 'familia', 'preco_venda', 'estoque_atual', 'ativo')
    autocomplete_fields = ('produto',)


class PagamentoVendaInline(admin.TabularInline):
    model = PagamentoVenda
    extra = 0
    fields = ('tipo', 'valor')
    readonly_fields = ('tipo', 'valor')


class ItemVendaMobileInline(admin.TabularInline):
    model = ItemVendaMobile
    extra = 0
    fields = ('nome_produto', 'familia_produto', 'quantidade', 'preco_unitario', 'desconto_perc', 'total_item')
    readonly_fields = ('nome_produto', 'familia_produto', 'quantidade', 'preco_unitario', 'desconto_perc', 'total_item')


class EntradaEstoqueLocalInline(admin.TabularInline):
    model = EntradaEstoqueLocal
    extra = 0
    fields = ('quantidade', 'preco_custo', 'preco_venda', 'data', 'criado_por', 'criado_em')
    readonly_fields = ('criado_em',)


# ---------------------------------------------------------------------------
# ADMINS
# ---------------------------------------------------------------------------

@admin.register(LocalVenda)
class LocalVendaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'evento', 'ativo', 'modulo_pdv', 'modulo_dashboard', 'modulo_estoque')
    list_filter = ('evento', 'ativo')
    search_fields = ('nome', 'evento__nome')
    inlines = [FamiliaVendaInline, ProdutoLocalInline]


@admin.register(FamiliaVenda)
class FamiliaVendaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'local')
    list_filter = ('local__evento', 'local')
    search_fields = ('nome', 'local__nome')


@admin.register(ProdutoLocal)
class ProdutoLocalAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'familia', 'preco_venda', 'estoque_atual', 'status_estoque', 'ativo')
    list_filter = ('local__evento', 'local', 'familia', 'ativo')
    search_fields = ('produto__nome', 'produto__sku', 'local__nome')
    autocomplete_fields = ('produto',)
    inlines = [EntradaEstoqueLocalInline]

    @admin.display(description='Status Estoque')
    def status_estoque(self, obj):
        return obj.status_estoque


@admin.register(EntradaEstoqueLocal)
class EntradaEstoqueLocalAdmin(admin.ModelAdmin):
    list_display = ('produto_local', 'quantidade', 'preco_custo', 'preco_venda', 'data', 'criado_por')
    list_filter = ('produto_local__local__evento', 'produto_local__local', 'data')
    search_fields = ('produto_local__produto__nome',)
    readonly_fields = ('criado_em',)


@admin.register(VendaMobile)
class VendaMobileAdmin(admin.ModelAdmin):
    list_display = ('id_referencia', 'evento', 'local', 'vendedor', 'total', 'data_hora')
    list_filter = ('evento', 'local', 'data_hora')
    search_fields = ('id_referencia', 'vendedor__username')
    readonly_fields = ('data_hora',)
    inlines = [PagamentoVendaInline, ItemVendaMobileInline]


@admin.register(PagamentoVenda)
class PagamentoVendaAdmin(admin.ModelAdmin):
    list_display = ('venda', 'tipo', 'valor')
    list_filter = ('tipo',)
