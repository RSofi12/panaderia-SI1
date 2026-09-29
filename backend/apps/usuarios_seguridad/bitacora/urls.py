from django.urls import path

from .views import BitacoraListView, BitacoraOpcionesView

app_name = 'bitacora'

urlpatterns = [
    path('bitacora/', BitacoraListView.as_view(), name='lista'),
    path('bitacora/opciones/', BitacoraOpcionesView.as_view(), name='opciones'),
]
