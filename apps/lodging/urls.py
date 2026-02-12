from django.urls import path
from . import views

app_name = "lodging"

urlpatterns = [
    path("lodging/chales/", views.chales_lista, name="chales_lista"),
    path("lodging/chales/novo/", views.chale_criar, name="chale_criar"),
    path("lodging/chales/<int:chale_id>/editar/", views.chale_editar, name="chale_editar"),
    path("lodging/reservas/", views.reservas_lista, name="reservas_lista"),
    path("lodging/reservas/nova/", views.reserva_criar, name="reserva_criar"),
    path("lodging/reservas/<int:reserva_id>/editar/", views.reserva_editar, name="reserva_editar"),
    path("lodging/reservas/<int:reserva_id>/excluir/", views.reserva_excluir, name="reserva_excluir"),
    path("lodging/mapa/", views.mapa_chales, name="mapa_chales"),
]
