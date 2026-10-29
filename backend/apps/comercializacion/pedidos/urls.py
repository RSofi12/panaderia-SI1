from django.urls import path

from apps.comercializacion.pedidos.views import (
    PedidoCreateView,
    PedidoDetailView,
    PedidoEstadoDetailView,
    PedidoEstadoListView,
)

app_name = 'pedidos'

urlpatterns = [
    path('estado/', PedidoEstadoListView.as_view(), name='estado-lista'),
    path('estado/<int:pk>/', PedidoEstadoDetailView.as_view(), name='estado-detalle'),
    path('', PedidoCreateView.as_view(), name='alta'),
    path('<int:pk>/', PedidoDetailView.as_view(), name='detalle'),
]
