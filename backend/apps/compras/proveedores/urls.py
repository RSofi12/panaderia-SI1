from django.urls import path

from .views import (
    ProveedorDetailView,
    ProveedorListCreateView,
    ProveedorToggleActivoView,
)

app_name = 'proveedores'

urlpatterns = [
    path('', ProveedorListCreateView.as_view(), name='proveedores'),
    path('<int:pk>/', ProveedorDetailView.as_view(), name='proveedor_detalle'),
    path(
        '<int:pk>/toggle-activo/',
        ProveedorToggleActivoView.as_view(),
        name='proveedor_toggle_activo',
    ),
]
