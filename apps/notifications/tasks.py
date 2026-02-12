from django.utils import timezone
from django.conf import settings
from .models import ReminderConfig
from twilio.rest import Client
import os
import logging

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://127.0.0.1:8001').rstrip('/')


def enviar_lembretes():
    """Tarefa agendada para verificar e enviar lembretes de eventos"""

    # Validar credenciais do Twilio
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        logger.debug(
            "Credenciais do Twilio não configuradas no .env - lembretes desativados")
        return

    agora = timezone.now()

    # Lembretes ativos que ainda não foram enviados
    reminders = ReminderConfig.objects.filter(
        ativo=True,
        enviado=False,
        data_hora_envio__isnull=False,
    )

    for reminder in reminders:
        tempo_envio = reminder.data_hora_envio

        # Verificar se estamos dentro da janela de envio (±5 minutos)
        diferenca_segundos = abs((agora - tempo_envio).total_seconds())

        if diferenca_segundos < 300:  # Dentro de 5 minutos
            try:
                _enviar_mensagem_whatsapp(reminder)
            except Exception as e:
                logger.error(
                    f"Erro ao enviar lembrete {reminder.id}: {str(e)}")


def _enviar_mensagem_whatsapp(reminder):
    """Função auxiliar para enviar mensagem de WhatsApp"""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        mensagem = reminder.mensagem_renderizada()

        media_urls = []
        if reminder.midia_url:
            media_urls.append(reminder.midia_url)
        elif reminder.midia:
            media_urls.append(f"{APP_BASE_URL}{settings.MEDIA_URL}{reminder.midia.name}")

        # Enviar mensagem
        payload = {
            "from_": TWILIO_WHATSAPP_NUMBER,
            "body": mensagem,
            "to": f'whatsapp:{reminder.telefone}',
        }
        if media_urls:
            payload["media_url"] = media_urls

        message = client.messages.create(
            **payload
        )

        # Marcar como enviado
        reminder.enviado = True
        reminder.save()

        logger.info(
            f"✓ Lembrete enviado para {reminder.telefone} (SID: {message.sid})")

    except Exception as e:
        logger.error(
            f"✗ Erro ao enviar mensagem para {reminder.telefone}: {str(e)}")
        raise
