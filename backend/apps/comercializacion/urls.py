from django.urls import include, path

app_name = 'comercializacion'

urlpatterns = [
    path('ventas/', include('apps.comercializacion.ventas.urls')),
]
