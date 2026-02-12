from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.lembretes_lista, name="lembretes_lista"),
    path("notifications/novo/", views.lembrete_criar, name="lembrete_criar"),
    path("notifications/<int:lembrete_id>/editar/",
         views.lembrete_editar, name="lembrete_editar"),
    path("notifications/<int:lembrete_id>/excluir/",
         views.lembrete_excluir, name="lembrete_excluir"),
    path("notifications/<int:lembrete_id>/resetar/",
         views.lembrete_resetar, name="lembrete_resetar"),
]
