"""
Cierre estático del CU24 (Reporte de compras y gastos).

Usa el mismo cálculo que el reporte dinámico y guarda el resultado.
Después de guardarlo, leer esta tabla no vuelve a sumar compras.
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.reportes.models import CierreReporteCompras, LineaCierreReporteCompras, PeriodoReporte
from apps.reportes.services.reporte_compras import reporte_compras
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def cierre_como_reporte(cierre: CierreReporteCompras) -> dict:
    return {
        'id_cierre': cierre.id_cierre,
        'desde': cierre.desde,
        'hasta': cierre.hasta,
        'periodo': cierre.periodo,
        'proveedor': cierre.id_proveedor.nombre if cierre.id_proveedor else None,
        'cantidad': cierre.cantidad,
        'total': cierre.total,
        'fecha_generacion': cierre.fecha_generacion,
        'generado_por': cierre.id_usuario.nombre_usuario,
        'insumos': [
            {
                'nombre': linea.nombre_materia_prima,
                'unidad_medida': linea.unidad_medida,
                'cantidad': linea.cantidad,
                'subtotal': linea.subtotal,
            }
            for linea in cierre.lineas.all()
        ],
    }


def listar_cierres_compras():
    return (
        CierreReporteCompras.objects.select_related('id_usuario', 'id_proveedor')
        .prefetch_related('lineas')
        .all()
    )


@transaction.atomic
def guardar_cierre_compras(*, usuario, desde: date, hasta: date, periodo: str, id_proveedor=None) -> dict:
    if periodo not in PeriodoReporte.values:
        raise ValidationError({'periodo': 'El periodo debe ser día, semana o mes.'})

    reporte = reporte_compras(desde=desde, hasta=hasta, id_proveedor=id_proveedor)
    cierre = CierreReporteCompras.objects.create(
        desde=reporte['desde'],
        hasta=reporte['hasta'],
        periodo=periodo,
        id_proveedor_id=id_proveedor or None,
        cantidad=reporte['cantidad'],
        total=reporte['total'],
        id_usuario=usuario,
    )
    LineaCierreReporteCompras.objects.bulk_create([
        LineaCierreReporteCompras(
            id_cierre=cierre,
            nombre_materia_prima=insumo['nombre'],
            unidad_medida=insumo['unidad_medida'],
            cantidad=insumo['cantidad'],
            subtotal=insumo['subtotal'],
        )
        for insumo in reporte['insumos']
    ])
    nombre_prov = cierre.id_proveedor.nombre if cierre.id_proveedor else 'todos los proveedores'
    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.CIERRE_REPORTE_COMPRAS,
        tabla_afectada='cierre_reporte_compras',
        descripcion=(
            f'Cierre de compras {periodo} del {desde} al {hasta}, proveedor {nombre_prov}, '
            f'{reporte["cantidad"]} compras, Bs {reporte["total"]:.2f}.'
        ),
    )
    cierre = listar_cierres_compras().get(pk=cierre.pk)
    return cierre_como_reporte(cierre)
