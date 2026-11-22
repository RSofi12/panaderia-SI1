from django.urls import path

from apps.reportes.views import (
    CierreReporteComprasDetailView,
    CierreReporteComprasPdfView,
    CierresReporteComprasView,
    CierreReporteVentasDetailView,
    CierreReporteVentasPdfView,
    CierresReporteVentasView,
    ReporteComprasCsvView,
    ReporteComprasView,
    ReporteVentasCsvView,
    ReporteVentasView,
)

app_name = 'reportes'

urlpatterns = [
    # CU21: Reporte de ventas
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
]
