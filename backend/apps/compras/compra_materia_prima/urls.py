from django.urls import path

from .views import CompraDetailView, CompraListCreateView

app_name = 'compra_materia_prima'

urlpatterns = [
    path('', CompraListCreateView.as_view(), name='compras'),
    path('<int:pk>/', CompraDetailView.as_view(), name='compra_detalle'),
]
