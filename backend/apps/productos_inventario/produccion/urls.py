from django.urls import path

from .views import (
    InventarioProductoTerminadoListView,
    ProduccionListCreateView,
)

urlpatterns = [
    path('produccion/', ProduccionListCreateView.as_view(), name='produccion-list-create'),
    path(
        'productos-terminados/existencias/',
        InventarioProductoTerminadoListView.as_view(),
        name='productos-terminados-existencias',
    ),
]
