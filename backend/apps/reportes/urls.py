from django.urls import path

from apps.reportes.views import (
    ReporteExistenciasView,
    ReporteInterpretarVozView,
    ReporteVentasCsvView,
    ReporteVentasPdfView,
    ReporteVentasView,
)

app_name = 'reportes'

urlpatterns = [
    path('reportes/existencias/', ReporteExistenciasView.as_view(), name='reporte-existencias'),
    path('reportes/voz/interpretar/', ReporteInterpretarVozView.as_view(), name='reporte-voz-interpretar'),
    path('reportes/ventas/', ReporteVentasView.as_view(), name='reporte-ventas'),
    path('reportes/ventas/csv/', ReporteVentasCsvView.as_view(), name='reporte-ventas-csv'),
    path('reportes/ventas/pdf/', ReporteVentasPdfView.as_view(), name='reporte-ventas-pdf'),
]
