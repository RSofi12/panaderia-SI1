from django.urls import path

from .views import ProduccionDetailView, ProduccionListView

urlpatterns = [
    path('produccion/', ProduccionListView.as_view(), name='produccion-list'),
    path('produccion/<int:id_produccion>/', ProduccionDetailView.as_view(), name='produccion-detail'),
]
