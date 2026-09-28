from django.urls import path

from .views import (
    CategoriaProductoListView,
    ProductoDetailView,
    ProductoListCreateView,
    ProductoToggleActivoView,
)

app_name = 'productos_inventario'

urlpatterns = [
    path('categorias-producto/', CategoriaProductoListView.as_view(), name='categorias_producto'),
    path('productos/', ProductoListCreateView.as_view(), name='productos'),
    path('productos/<int:pk>/', ProductoDetailView.as_view(), name='producto_detalle'),
    path('productos/<int:pk>/toggle-activo/', ProductoToggleActivoView.as_view(), name='producto_toggle_activo'),
]
