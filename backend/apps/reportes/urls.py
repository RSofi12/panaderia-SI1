from django.urls import path

from apps.reportes.views import (
    CierreReporteComprasDetailView,
    CierreReporteComprasPdfView,
    CierresReporteComprasView,
    ReporteAnalizarVozCsvView,
    ReporteAnalizarVozPdfView,
    ReporteAnalizarVozView,
    ReporteComprasCsvView,
    ReporteComprasView,
    ReporteExistenciasView,
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
    # CU21: Reporte de ventas y comandos por voz
    path('reportes/ventas/', ReporteVentasView.as_view(), name='reporte-ventas'),
    path('reportes/ventas/csv/', ReporteVentasCsvView.as_view(), name='reporte-ventas-csv'),
    path('reportes/ventas/pdf/', ReporteVentasPdfView.as_view(), name='reporte-ventas-pdf'),
    path('reportes/voz/analizar/', ReporteAnalizarVozView.as_view(), name='reporte-voz-analizar'),
    path('reportes/voz/analizar/pdf/', ReporteAnalizarVozPdfView.as_view(), name='reporte-voz-analizar-pdf'),
    path('reportes/voz/analizar/csv/', ReporteAnalizarVozCsvView.as_view(), name='reporte-voz-analizar-csv'),
    path('reportes/voz/interpretar/', ReporteInterpretarVozView.as_view(), name='reporte-voz-interpretar'),

    # CU23: Reporte de existencias
    path('reportes/existencias/', ReporteExistenciasView.as_view(), name='reporte-existencias'),

    # CU24: Reporte de compras y gastos
    path('reportes/compras/', ReporteComprasView.as_view(), name='reporte-compras'),
    path('reportes/compras/csv/', ReporteComprasCsvView.as_view(), name='reporte-compras-csv'),
    path('reportes/compras/cierres/', CierresReporteComprasView.as_view(), name='cierres-reporte-compras'),
    path(
        'reportes/compras/cierres/<int:id_cierre>/pdf/',
        CierreReporteComprasPdfView.as_view(),
        name='cierre-reporte-compras-pdf',
    ),
    path(
        'reportes/compras/cierres/<int:id_cierre>/',
        CierreReporteComprasDetailView.as_view(),
        name='cierre-reporte-compras',
    ),

    # CU25: Reporte de resultados económicos
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
