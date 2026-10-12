from django.urls import include, path

app_name = 'compras'

urlpatterns = [
    path('proveedores/', include('apps.compras.proveedores.urls')),
    path('compras/', include('apps.compras.compra_materia_prima.urls')),
]
