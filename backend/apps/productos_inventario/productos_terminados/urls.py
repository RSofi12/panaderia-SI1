from django.urls import path

from .views import (
    InventarioProductoTerminadoListView,
    NotaPerdidaProductoListCreateView,
)

urlpatterns = [
    path(
        'productos-terminados/existencias/',
        InventarioProductoTerminadoListView.as_view(),
        name='productos-terminados-existencias',
    ),
    path(
        'productos-terminados/mermas/',
        NotaPerdidaProductoListCreateView.as_view(),
        name='productos-terminados-mermas',
    ),
]
