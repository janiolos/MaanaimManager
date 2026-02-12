from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("inventory/produtos/", views.produtos_lista, name="produtos_lista"),
    path("inventory/produtos/novo/", views.produto_criar, name="produto_criar"),
    path("inventory/entradas/nova/", views.entrada_criar, name="entrada_criar"),
    path("inventory/movimentos/", views.movimentos_lista, name="movimentos_lista"),
    path("inventory/movimentos/novo/", views.movimentacao_criar, name="movimentacao_criar"),
]
