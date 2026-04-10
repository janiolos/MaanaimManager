from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_mobile_view, name='pos_mobile'),
    path('api/dados/', views.api_dados_iniciais, name='api_dados'),
    path('api/venda/', views.api_post_venda, name='api_venda'),
]
