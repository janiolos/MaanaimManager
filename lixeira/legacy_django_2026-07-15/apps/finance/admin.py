from django.contrib import admin

from .models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro, AnexoLancamento


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo")
    list_filter = ("tipo",)
    search_fields = ("nome",)


@admin.register(ContaCaixa)
class ContaCaixaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("descricao", "tipo", "valor", "data", "evento")
    list_filter = ("tipo", "data", "evento")
    search_fields = ("descricao",)


@admin.register(AnexoLancamento)
class AnexoLancamentoAdmin(admin.ModelAdmin):
    list_display = ("lancamento", "arquivo", "enviado_em")
    search_fields = ("descricao",)
