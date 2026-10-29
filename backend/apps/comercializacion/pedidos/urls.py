from django.urls import path

from apps.comercializacion.pedidos.views import PedidoCreateView, PedidoDetailView

app_name = 'pedidos'

urlpatterns = [
    path('', PedidoCreateView.as_view(), name='alta'),
    path('<int:pk>/', PedidoDetailView.as_view(), name='detalle'),
]
