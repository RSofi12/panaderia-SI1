from django.urls import path

from apps.productos_inventario.produccion.views import RecetasListView
from apps.productos_inventario.productos.views import (
    CategoriaProductoListView,
    HistorialPreciosListView,
    ProductoDetailView,
    ProductoListCreateView,
    ProductoToggleActivoView,
)

urlpatterns = [
    path('categorias-producto/', CategoriaProductoListView.as_view(), name='categorias_producto'),
    path('productos/', ProductoListCreateView.as_view(), name='productos'),
    path('productos/historial-precios/', HistorialPreciosListView.as_view(), name='historial_precios'),
    path('productos/recetas/', RecetasListView.as_view(), name='productos_recetas'),
    path('productos/<int:pk>/', ProductoDetailView.as_view(), name='producto_detalle'),
    path('productos/<int:pk>/toggle-activo/', ProductoToggleActivoView.as_view(), name='producto_toggle_activo'),
]
