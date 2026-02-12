from django.contrib import admin

from .models import Chale, ReservaChale


@admin.register(Chale)
class ChaleAdmin(admin.ModelAdmin):
    list_display = ("codigo", "capacidade", "status", "acessivel_cadeirante")
    list_filter = ("status", "acessivel_cadeirante")
    search_fields = ("codigo",)


@admin.register(ReservaChale)
class ReservaChaleAdmin(admin.ModelAdmin):
    list_display = (
        "evento",
        "chale",
        "responsavel_nome",
        "qtd_pessoas",
        "status",
        "valor_adicional",
    )
    list_filter = ("status", "evento", "chale")
    search_fields = ("responsavel_nome",)
