from django.urls import path

from .views import (
    ProveedorDetailView,
    ProveedorListCreateView,
    ProveedorToggleActivoView,
)

app_name = 'compras'

urlpatterns = [
    path('proveedores/', ProveedorListCreateView.as_view(), name='proveedores'),
    path('proveedores/<int:pk>/', ProveedorDetailView.as_view(), name='proveedor_detalle'),
    path(
        'proveedores/<int:pk>/toggle-activo/',
        ProveedorToggleActivoView.as_view(),
        name='proveedor_toggle_activo',
    ),
]
