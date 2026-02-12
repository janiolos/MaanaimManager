from .models import Evento


def get_evento_atual(request):
    evento_id = request.session.get("evento_id")
    if not evento_id:
        return None
    try:
        return Evento.objects.get(id=evento_id)
    except Evento.DoesNotExist:
        return None
