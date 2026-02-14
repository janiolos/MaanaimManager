from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("core/dashboard/", views.dashboard, name="dashboard"),
    path("core/evento/", views.selecionar_evento, name="selecionar_evento"),
    path("core/eventos/", views.eventos_lista, name="eventos_lista"),
    path("core/eventos/novo/", views.evento_criar, name="evento_criar"),
    path("core/eventos/<int:evento_id>/editar/", views.evento_editar, name="evento_editar"),
    path("api/v1/health/", views.api_health, name="api_health"),
    path("api/v1/dashboard/", views.api_dashboard, name="api_dashboard"),
]
