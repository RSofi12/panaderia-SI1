from django.urls import path

from .views import (
    ExistenciasListView,
    KardexProductoTerminadoView,
    NotaPerdidaProductoListCreateView,
    ResumenExistenciasView,
)

app_name = 'productos_terminados'

urlpatterns = [
    # CU12: Consultar existencias de productos terminados
    path(
        'productos-terminados/existencias/',
        ExistenciasListView.as_view(),
        name='existencias-list',
    ),
    path(
        'productos-terminados/existencias/resumen/',
        ResumenExistenciasView.as_view(),
        name='existencias-resumen',
    ),
    path(
        'productos-terminados/existencias/<int:id_producto>/movimientos/',
        KardexProductoTerminadoView.as_view(),
        name='existencias-kardex',
    ),

    # CU18: Bajas y Mermas de productos terminados (Ciclo 3)
    path(
        'productos-terminados/mermas/',
        NotaPerdidaProductoListCreateView.as_view(),
        name='productos-terminados-mermas',
    ),
]
