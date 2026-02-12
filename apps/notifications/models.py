from django.db import models
from apps.core.models import Evento


class ReminderConfig(models.Model):
    """Configuração de lembretes para eventos"""
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='reminders')
    # Campo legado mantido para compatibilidade com dados antigos
    intervalo = models.CharField(max_length=10, blank=True, default='24h')
    data_hora_envio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora exatas para envio do lembrete.",
    )
    telefone = models.CharField(
        max_length=20, help_text="Formato: +55xxxxxxxxxx")
    mensagem = models.TextField(
        blank=True,
        help_text=(
            "Mensagem personalizada. Placeholders: "
            "{evento_nome}, {data_evento}, {intervalo}."
        ),
    )
    midia = models.FileField(
        upload_to="whatsapp/",
        blank=True,
        null=True,
        help_text="Opcional: imagem/figurinha para enviar junto com a mensagem.",
    )
    midia_url = models.URLField(
        blank=True,
        help_text="Opcional: URL publica de imagem/figurinha para envio via WhatsApp.",
    )
    ativo = models.BooleanField(default=True)
    enviado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Lembrete"
        verbose_name_plural = "Configurações de Lembretes"
        unique_together = ['evento', 'data_hora_envio', 'telefone']
        ordering = ['-criado_em']

    def __str__(self):
        if self.data_hora_envio:
            return f"{self.evento.nome} - {self.data_hora_envio:%d/%m/%Y %H:%M}"
        return f"{self.evento.nome} - sem agendamento"

    def mensagem_renderizada(self):
        data_evento = self.evento.data_inicio.strftime("%d/%m/%Y as %H:%M")
        intervalo_label = (
            self.data_hora_envio.strftime("%d/%m/%Y as %H:%M")
            if self.data_hora_envio
            else "Nao informado"
        )
        template = self.mensagem.strip() if self.mensagem else ""
        if not template:
            template = (
                "🔔 *Lembrete - {evento_nome}*\n\n"
                "📅 Data: {data_evento}\n"
                "⏱️ Envio: {intervalo}\n\n"
                "Falta pouco para comecar! 🎉"
            )
        return template.format(
            evento_nome=self.evento.nome,
            data_evento=data_evento,
            intervalo=intervalo_label,
        )
