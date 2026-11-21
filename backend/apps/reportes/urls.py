from django.urls import path

from apps.reportes.views import (
    ReporteInterpretarVozView,
    ReporteResultadosEconomicosCsvView,
    ReporteResultadosEconomicosPdfView,
    ReporteResultadosEconomicosView,
    ReporteVentasCsvView,
    ReporteVentasPdfView,
    ReporteVentasView,
)

app_name = 'reportes'

urlpatterns = [
    path('reportes/voz/interpretar/', ReporteInterpretarVozView.as_view(), name='reporte-voz-interpretar'),
    path('reportes/ventas/', ReporteVentasView.as_view(), name='reporte-ventas'),
    path('reportes/ventas/csv/', ReporteVentasCsvView.as_view(), name='reporte-ventas-csv'),
    path('reportes/ventas/pdf/', ReporteVentasPdfView.as_view(), name='reporte-ventas-pdf'),
    path(
        'reportes/resultados-economicos/',
        ReporteResultadosEconomicosView.as_view(),
        name='reporte-resultados-economicos',
    ),
    path(
        'reportes/resultados-economicos/csv/',
        ReporteResultadosEconomicosCsvView.as_view(),
        name='reporte-resultados-economicos-csv',
    ),
    path(
        'reportes/resultados-economicos/pdf/',
        ReporteResultadosEconomicosPdfView.as_view(),
        name='reporte-resultados-economicos-pdf',
    ),
]
