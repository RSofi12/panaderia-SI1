from django.urls import path

from apps.productos_inventario.materia_prima.views import MateriaPrimaListView


urlpatterns = [
    path('materias-primas/', MateriaPrimaListView.as_view(), name='materias_primas'),
]
