from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("finance/categorias/", views.categorias_por_tipo, name="categorias_por_tipo"),
    path("finance/lancamentos/", views.lancamentos_lista, name="lancamentos_lista"),
    path("finance/lancamentos/novo/", views.lancamento_criar, name="lancamento_criar"),
    path("finance/lancamentos/<int:lancamento_id>/editar/", views.lancamento_editar, name="lancamento_editar"),
    path("finance/lancamentos/<int:lancamento_id>/excluir/", views.lancamento_excluir, name="lancamento_excluir"),
    path("finance/lancamentos/<int:lancamento_id>/anexos/", views.anexos, name="anexos"),
    path("finance/relatorios/", views.relatorios_index, name="relatorios_index"),
    path("finance/relatorios/evento/", views.relatorio_evento, name="relatorio_evento"),
    path("finance/relatorios/detalhado/", views.relatorio_detalhado, name="relatorio_detalhado"),
    path("finance/relatorios/conciliacao/", views.relatorio_conciliacao, name="relatorio_conciliacao"),
    path("finance/relatorios/fluxo-caixa/", views.relatorio_fluxo_caixa, name="relatorio_fluxo_caixa"),
    path("finance/relatorios/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
]
