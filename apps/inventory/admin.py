from django.contrib import admin

from .models import EntradaEstoque, MovimentoEstoque, Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sku", "unidade", "estoque_atual", "estoque_minimo", "estoque_maximo", "ativo")
    list_filter = ("ativo",)
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
