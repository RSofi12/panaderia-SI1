from django.urls import path

from apps.reportes.views import (
    CierreReporteVentasDetailView,
    CierreReporteVentasPdfView,
    CierresReporteVentasView,
    ReporteVentasCsvView,
    ReporteVentasView,
)

app_name = 'reportes'

urlpatterns = [
    path('reportes/ventas/', ReporteVentasView.as_view(), name='reporte-ventas'),
    path('reportes/ventas/csv/', ReporteVentasCsvView.as_view(), name='reporte-ventas-csv'),
    path('reportes/ventas/cierres/', CierresReporteVentasView.as_view(), name='cierres-reporte-ventas'),
    path(
        'reportes/ventas/cierres/<int:id_cierre>/pdf/',
        CierreReporteVentasPdfView.as_view(),
        name='cierre-reporte-ventas-pdf',
    ),
    path(
        'reportes/ventas/cierres/<int:id_cierre>/',
        CierreReporteVentasDetailView.as_view(),
        name='cierre-reporte-ventas',
    ),
]
