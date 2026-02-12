from django.apps import AppConfig
import os


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        """Inicializa o scheduler de lembretes quando dependencias estao disponiveis."""
        if os.environ.get("RUN_MAIN") != "true":
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django_apscheduler.jobstores import DjangoJobStore
            from .tasks import enviar_lembretes

            scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
            scheduler.add_jobstore(DjangoJobStore(), "default")

            # Remove job anterior se existir
            try:
                scheduler.remove_job('enviar_lembretes')
            except Exception:
                pass

            # Registra o job
            scheduler.add_job(
                enviar_lembretes,
                'interval',
                minutes=5,
                id='enviar_lembretes',
                name='Enviar lembretes de eventos',
                replace_existing=True
            )
            scheduler.start()
        except Exception:
            return
