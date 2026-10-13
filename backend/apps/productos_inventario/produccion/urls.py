from django.urls import path

from .views import (
    ProduccionDetailView,
    ProduccionListView,
    ProduccionSimularView,
    RecetasListView,
)

urlpatterns = [
    path('produccion/', ProduccionListView.as_view(), name='produccion-list'),
    path('produccion/simular/', ProduccionSimularView.as_view(), name='produccion-simular'),
    path('produccion/recetas/', RecetasListView.as_view(), name='produccion-recetas'),
    path('produccion/<int:id_produccion>/', ProduccionDetailView.as_view(), name='produccion-detail'),
]
