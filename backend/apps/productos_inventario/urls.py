from django.urls import include, path

app_name = 'productos_inventario'

urlpatterns = [
    path('', include('apps.productos_inventario.productos.urls')),
    path('', include('apps.productos_inventario.materia_prima.urls')),
]
