"""
Cierre estático del CU21.

Usa el mismo cálculo que el reporte dinámico y guarda el resultado.
Después de guardarlo, leer esta tabla no vuelve a sumar venta.
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.reportes.models import CierreReporteVentas, LineaCierreReporteVentas, PeriodoReporte
from apps.reportes.services.reporte_ventas import reporte_ventas
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def cierre_como_reporte(cierre: CierreReporteVentas) -> dict:
    return {
        'id_cierre': cierre.id_cierre,
        'desde': cierre.desde,
        'hasta': cierre.hasta,
        'periodo': cierre.periodo,
        'metodo_pago': cierre.metodo_pago,
        'cantidad': cierre.cantidad,
        'total': cierre.total,
        'efectivo': cierre.efectivo,
        'tarjeta': cierre.tarjeta,
        'fecha_generacion': cierre.fecha_generacion,
        'generado_por': cierre.id_usuario.nombre_usuario,
        'productos': [
            {
                'nombre': linea.nombre_producto,
                'cantidad': linea.cantidad,
                'subtotal': linea.subtotal,
            }
            for linea in cierre.lineas.all()
        ],
    }


def listar_cierres():
    return CierreReporteVentas.objects.select_related('id_usuario').prefetch_related('lineas')


@transaction.atomic
def guardar_cierre(*, usuario, desde: date, hasta: date, periodo: str, metodo_pago=None) -> dict:
    if periodo not in PeriodoReporte.values:
        raise ValidationError({'periodo': 'El periodo debe ser día, semana o mes.'})

    reporte = reporte_ventas(desde=desde, hasta=hasta, metodo_pago=metodo_pago)
    cierre = CierreReporteVentas.objects.create(
        desde=reporte['desde'],
        hasta=reporte['hasta'],
        periodo=periodo,
        metodo_pago=metodo_pago or None,
        cantidad=reporte['cantidad'],
        total=reporte['total'],
        efectivo=reporte['efectivo'],
        tarjeta=reporte['tarjeta'],
        id_usuario=usuario,
    )
    LineaCierreReporteVentas.objects.bulk_create([
        LineaCierreReporteVentas(
            id_cierre=cierre,
            nombre_producto=producto['nombre'],
            cantidad=producto['cantidad'],
            subtotal=producto['subtotal'],
        )
        for producto in reporte['productos']
    ])
    metodo = metodo_pago or 'todos'
    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.CIERRE_REPORTE_VENTAS,
        tabla_afectada='cierre_reporte_ventas',
        descripcion=(
            f'Cierre {periodo} del {desde} al {hasta}, método {metodo}, '
            f'{reporte["cantidad"]} ventas, Bs {reporte["total"]}.'
        ),
    )
    cierre = listar_cierres().get(pk=cierre.pk)
    return cierre_como_reporte(cierre)
