from django.urls import path

from apps.comercializacion.pedidos.views import (
    PedidoCreateView,
    PedidoDetailView,
    PedidoEstadoDetailView,
    PedidoEstadoListView,
    PedidoStripeCarritoView,
    PedidoStripeConfigView,
    PedidoStripeIntencionView,
)

app_name = 'pedidos'

urlpatterns = [
    path('estado/', PedidoEstadoListView.as_view(), name='estado-lista'),
    path('estado/<int:pk>/', PedidoEstadoDetailView.as_view(), name='estado-detalle'),
    path('', PedidoCreateView.as_view(), name='alta'),
    path('stripe/config/', PedidoStripeConfigView.as_view(), name='stripe-config'),
    path('stripe/intencion/', PedidoStripeCarritoView.as_view(), name='stripe-carrito'),
    path('<int:pk>/stripe/intencion/', PedidoStripeIntencionView.as_view(), name='stripe-intencion'),
    path('<int:pk>/', PedidoDetailView.as_view(), name='detalle'),
]
