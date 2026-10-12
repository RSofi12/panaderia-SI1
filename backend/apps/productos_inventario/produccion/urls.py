from django.urls import path

from .views import ProduccionListCreateView

urlpatterns = [
    path('produccion/', ProduccionListCreateView.as_view(), name='produccion-list-create'),
]
