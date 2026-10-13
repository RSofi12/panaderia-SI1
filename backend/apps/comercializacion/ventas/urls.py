from django.urls import path

from apps.comercializacion.ventas.views import (
    IntencionStripeView,
    VentaDetailView,
    VentaListCreateView,
)

app_name = 'ventas'

urlpatterns = [
    path('stripe/intencion/', IntencionStripeView.as_view(), name='stripe-intencion'),
    path('', VentaListCreateView.as_view(), name='lista'),
    path('<int:pk>/', VentaDetailView.as_view(), name='detalle'),
]
