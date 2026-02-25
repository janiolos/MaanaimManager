from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("inventory/dashboard/", views.dashboard, name="dashboard"),
    path("inventory/produtos/", views.produtos_lista, name="produtos_lista"),
    path("inventory/produtos/novo/", views.produto_criar, name="produto_criar"),
    path("inventory/entradas/nova/", views.entrada_criar, name="entrada_criar"),
    path("inventory/movimentos/", views.movimentos_lista, name="movimentos_lista"),
    path("inventory/requisicoes/", views.movimentos_lista, name="requisicoes_lista"),
    path("inventory/requisicoes/nova/", views.requisicao_criar, name="requisicao_criar"),
    path("inventory/requisicoes/<int:pk>/editar/", views.requisicao_editar, name="requisicao_editar"),
    path("inventory/movimentos/novo/", views.movimentacao_criar, name="movimentacao_criar"),
    path("inventory/requisicoes/<int:pk>/finalizar/", views.requisicao_finalizar, name="requisicao_finalizar"),
    path("inventory/requisicoes/<int:pk>/cancelar/", views.requisicao_cancelar, name="requisicao_cancelar"),
    path("inventory/requisicoes/<int:pk>/comprovante/", views.requisicao_comprovante, name="requisicao_comprovante"),
    path("inventory/fornecedores/", views.fornecedores_lista, name="fornecedores_lista"),
    path("inventory/fornecedores/novo/", views.fornecedor_criar, name="fornecedor_criar"),
    path("inventory/cotacoes/", views.cotacoes_lista, name="cotacoes_lista"),
    path("inventory/cotacoes/nova/", views.cotacao_criar, name="cotacao_criar"),
    path("inventory/cotacoes/<int:pk>/editar/", views.cotacao_editar, name="cotacao_editar"),
    path("inventory/cotacoes/<int:pk>/aprovar/", views.cotacao_aprovar, name="cotacao_aprovar"),
    path("inventory/cotacoes/<int:pk>/fechar/", views.cotacao_fechar, name="cotacao_fechar"),
    path("inventory/cotacoes/<int:pk>/cancelar/", views.cotacao_cancelar, name="cotacao_cancelar"),
    path("inventory/cotacoes/<int:pk>/comprovante/", views.cotacao_comprovante, name="cotacao_comprovante"),
]
