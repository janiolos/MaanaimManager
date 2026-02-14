from django.urls import path
from . import views

app_name = "lodging"

urlpatterns = [
    path("lodging/dashboard/", views.dashboard, name="dashboard"),
    path("lodging/chales/", views.chales_lista, name="chales_lista"),
    path("lodging/chales/novo/", views.chale_criar, name="chale_criar"),
    path("lodging/chales/<int:chale_id>/editar/", views.chale_editar, name="chale_editar"),
    path("lodging/reservas/", views.reservas_lista, name="reservas_lista"),
    path("lodging/reservas/nova/", views.reserva_criar, name="reserva_criar"),
    path("lodging/reservas/<int:reserva_id>/editar/", views.reserva_editar, name="reserva_editar"),
    path("lodging/reservas/<int:reserva_id>/excluir/", views.reserva_excluir, name="reserva_excluir"),
    path("lodging/mapa/", views.mapa_chales, name="mapa_chales"),
    path("lodging/acoes/nova/", views.acao_criar, name="acao_criar"),
    path("lodging/acoes/<int:acao_id>/editar/", views.acao_editar, name="acao_editar"),
    path("lodging/acoes/<int:acao_id>/excluir/", views.acao_excluir, name="acao_excluir"),
    path("lodging/chales/<int:chale_id>/acao/", views.chale_status_rapido, name="chale_status_rapido"),
]
