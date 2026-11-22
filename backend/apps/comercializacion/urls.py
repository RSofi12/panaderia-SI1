from django.urls import include, path

from .views import DisponibilidadProductosView

app_name = 'comercializacion'

urlpatterns = [
    path('ventas/', include('apps.comercializacion.ventas.urls')),
    path('pedidos/', include('apps.comercializacion.pedidos.urls')),
    path('disponibilidad/', DisponibilidadProductosView.as_view(), name='disponibilidad'),
]
