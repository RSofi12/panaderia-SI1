from django.urls import path

from .views import GastoAnularView, GastoDetailView, GastoListCreateView

app_name = 'gastos'

urlpatterns = [
    path('', GastoListCreateView.as_view(), name='list-create'),
    path('<int:pk>/', GastoDetailView.as_view(), name='detail'),
    path('<int:pk>/anular/', GastoAnularView.as_view(), name='anular'),
]
