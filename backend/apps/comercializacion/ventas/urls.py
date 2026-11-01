from django.urls import path

from apps.comercializacion.ventas.views import (
    IntencionStripeView,
    StripeConfigView,
    VentaDetailView,
    VentaComprobanteView,
    VentaComprobantePdfView,
    VentaListCreateView,
)

app_name = 'ventas'

urlpatterns = [
    path('stripe/config/', StripeConfigView.as_view(), name='stripe-config'),
    path('stripe/intencion/', IntencionStripeView.as_view(), name='stripe-intencion'),
    path('', VentaListCreateView.as_view(), name='lista'),
    path('<int:pk>/', VentaDetailView.as_view(), name='detalle'),
    path('<int:pk>/comprobante/', VentaComprobanteView.as_view(), name='comprobante'),
    path('<int:pk>/comprobante/pdf/', VentaComprobantePdfView.as_view(), name='comprobante-pdf'),
]

