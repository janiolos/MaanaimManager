from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    # ── SPA PDV ──────────────────────────────────────────────────────────────
    path('', views.pdv_view, name='pdv'),
    path('mobile/', views.pos_mobile_view, name='pos_mobile'),  # legado

    # ── API: Dados iniciais ───────────────────────────────────────────────────
    path('api/dados/', views.api_dados_iniciais, name='api_dados'),

    # ── API: Locais de Venda ──────────────────────────────────────────────────
    path('api/locais/', views.api_locais, name='api_locais'),
    path('api/locais/<int:local_id>/', views.api_local_detail, name='api_local_detail'),

    # ── API: Famílias ─────────────────────────────────────────────────────────
    path('api/familias/', views.api_familias, name='api_familias'),
    path('api/familias/<int:familia_id>/', views.api_familia_detail, name='api_familia_detail'),

    # ── API: Sub-Estoque (ProdutoLocal) ───────────────────────────────────────
    path('api/produtos-local/', views.api_produtos_local, name='api_produtos_local'),
    path('api/produtos-local/<int:pl_id>/', views.api_produto_local_detail, name='api_produto_local_detail'),

    # ── API: Entrada de Estoque no Local ──────────────────────────────────────
    path('api/estoque-local/entrada/', views.api_entrada_estoque_local, name='api_entrada_estoque_local'),

    # ── API: Vendas ───────────────────────────────────────────────────────────
    path('api/vendas/', views.api_vendas, name='api_vendas'),
    path('api/vendas/<int:venda_id>/', views.api_venda_detail, name='api_venda_detail'),

    # ── API legada (compatibilidade) ─────────────────────────────────────────
    path('api/venda/', views.api_vendas, name='api_venda'),
]
