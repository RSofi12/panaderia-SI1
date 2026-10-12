from django.urls import path

from apps.productos_inventario.materia_prima.views import (
    MateriaPrimaListView,
    MateriaPrimaStockListView,
)


urlpatterns = [
    path('materias-primas/', MateriaPrimaListView.as_view(), name='materias_primas'),
    path(
        'inventario/materias-primas/',
        MateriaPrimaStockListView.as_view(),
        name='materias_primas_stock',
    ),
]
