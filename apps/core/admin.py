from django.contrib import admin
from .models import AuditLog, CentroCusto, ConfiguracaoSistema, Evento


@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("codigo", "nome")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "data_inicio",
        "data_fim",
        "status",
        "fechado",
        "taxa_base",
        "taxa_trabalhador",
        "adicional_chale",
        "responsavel_geral",
        "centro_custo",
    )
    list_filter = ("status", "fechado", "ativo")
    search_fields = ("nome",)
    autocomplete_fields = ("responsavel_geral", "centro_custo")
    fieldsets = (
        ("Identificacao", {"fields": ("nome", "data_inicio", "data_fim", "status", "ativo", "fechado")}),
        (
            "Regras de Cobranca",
            {"fields": ("taxa_base", "taxa_trabalhador", "adicional_chale")},
        ),
        ("Planejamento", {"fields": ("prev_participantes", "prev_trabalhadores")}),
        ("Governanca", {"fields": ("responsavel_geral",)}),
        ("Centro de custo", {"fields": ("centro_custo",)}),
        ("Observacoes", {"fields": ("observacoes",)}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "method", "path", "status_code", "ip_address")
    list_filter = ("method", "status_code", "created_at")
    search_fields = ("path", "user__username", "view_name", "ip_address")
    readonly_fields = (
        "created_at",
        "user",
        "method",
        "path",
        "view_name",
        "status_code",
        "ip_address",
        "user_agent",
    )


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = (
        "nome_sistema",
        "rotulo_evento_singular",
        "rotulo_evento_plural",
        "modulo_financeiro_ativo",
        "modulo_estoque_ativo",
        "modulo_hospedagem_ativo",
        "modulo_notificacoes_ativo",
        "atualizado_em",
    )
