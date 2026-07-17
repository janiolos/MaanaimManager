from django.contrib import admin
from .models import ReminderConfig


@admin.register(ReminderConfig)
class ReminderConfigAdmin(admin.ModelAdmin):
    list_display = (
        'evento',
        'data_hora_envio',
        'telefone',
        'ativo',
        'enviado',
        'tem_mensagem_personalizada',
        'tem_midia',
        'criado_em',
    )
    list_filter = ('ativo', 'data_hora_envio', 'criado_em')
    search_fields = ('evento__nome', 'telefone')
    readonly_fields = ('criado_em', 'atualizado_em')

    fieldsets = (
        ('Configuração do Lembrete', {
            'fields': ('evento', 'data_hora_envio', 'telefone', 'mensagem', 'midia', 'midia_url', 'ativo')
        }),
        ('Status', {
            'fields': ('enviado',)
        }),
        ('Histórico', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    actions = ['resetar_lembretes']

    def resetar_lembretes(self, request, queryset):
        """Action para resetar o status de enviado"""
        updated = queryset.update(enviado=False)
        self.message_user(request, f'{updated} lembretes foram resetados.')
    resetar_lembretes.short_description = "Resetar lembretes selecionados"

    def tem_mensagem_personalizada(self, obj):
        return bool(obj.mensagem)

    tem_mensagem_personalizada.boolean = True
    tem_mensagem_personalizada.short_description = "Mensagem personalizada"

    def tem_midia(self, obj):
        return bool(obj.midia or obj.midia_url)

    tem_midia.boolean = True
    tem_midia.short_description = "Mídia"
