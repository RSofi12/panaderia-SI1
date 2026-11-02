from django.urls import path

from .views import CompraDetailView, CompraExportarView, CompraListCreateView

app_name = 'compra_materia_prima'

urlpatterns = [
    path('', CompraListCreateView.as_view(), name='compras'),
    path('csv/', CompraExportarView.as_view(formato='csv'), name='compras-csv'),
    path('pdf/', CompraExportarView.as_view(formato='pdf'), name='compras-pdf'),
    path('<int:pk>/', CompraDetailView.as_view(), name='compra_detalle'),
]
