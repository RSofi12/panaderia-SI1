from django.urls import path

from apps.productos_inventario.materia_prima.views import (
    AlertasBajoStockView,
    MateriaPrimaListView,
)

urlpatterns = [
    path(
        'materias-primas/',
        MateriaPrimaListView.as_view(),
        name='materias_primas',
    ),
    path(
        'materias-primas/alertas-bajo-stock/',
        AlertasBajoStockView.as_view(),
        name='alertas_bajo_stock',
    ),
]
