from django.urls import include, path

app_name = 'comercializacion'

urlpatterns = [
    path('ventas/', include('apps.comercializacion.ventas.urls')),
    path('pedidos/', include('apps.comercializacion.pedidos.urls')),
]
