from django.urls import path

from apps.productos_inventario.materia_prima.views import (
    MateriaPrimaDetailView,
    MateriaPrimaListView,
    MateriaPrimaStockListView,
    MateriaPrimaToggleActivoView,
)


urlpatterns = [
    path('materias-primas/', MateriaPrimaListView.as_view(), name='materias_primas'),
    path('materias-primas/<int:pk>/', MateriaPrimaDetailView.as_view(), name='materia_prima_detalle'),
    path(
        'materias-primas/<int:pk>/toggle-activo/',
        MateriaPrimaToggleActivoView.as_view(),
        name='materia_prima_toggle_activo',
    ),
    path(
        'inventario/materias-primas/',
        MateriaPrimaStockListView.as_view(),
        name='materias_primas_stock',
    ),
]
