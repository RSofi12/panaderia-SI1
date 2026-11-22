"""
Reporte dinámico de compras y gastos de materias primas (CU24).

Lee de compra y detalle_compra filtrando por fecha_hora.
Este servicio es de solo lectura y no escribe en la base de datos.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from apps.compras.compra_materia_prima.models import Compra, DetalleCompra

CERO = Decimal('0.00')
CERO_CANTIDAD = Decimal('0.000')


def reporte_compras(*, desde: date, hasta: date, id_proveedor=None, id_materia_prima=None) -> dict:
    if desde > hasta:
        raise ValidationError({'hasta': 'La fecha final no puede ser anterior a la inicial.'})

    compras = Compra.objects.filter(
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )
    if id_proveedor:
        compras = compras.filter(id_proveedor_id=id_proveedor)

    if id_materia_prima:
        compras = compras.filter(detalles__id_materia_prima_id=id_materia_prima).distinct()

    totales = compras.aggregate(
        cantidad_compras=Count('id_compra', distinct=True),
        suma_total=Coalesce(Sum('total'), CERO),
    )

    proveedores = (
        compras.values('id_proveedor__id_proveedor', 'id_proveedor__nombre')
        .annotate(
            cantidad_compras=Count('id_compra', distinct=True),
            total=Coalesce(Sum('total'), CERO),
        )
        .order_by('-total', 'id_proveedor__nombre')
    )

    detalles = DetalleCompra.objects.filter(id_compra__in=compras)
    if id_materia_prima:
        detalles = detalles.filter(id_materia_prima_id=id_materia_prima)

    insumos = (
        detalles.values(
            'id_materia_prima__id_materia_prima',
            'id_materia_prima__nombre',
            'id_materia_prima__unidad_medida',
        )
        .annotate(
            cantidad=Coalesce(Sum('cantidad'), CERO_CANTIDAD),
            subtotal=Coalesce(Sum('subtotal'), CERO),
        )
        .order_by('-subtotal', 'id_materia_prima__nombre')
    )

    return {
        'desde': desde,
        'hasta': hasta,
        'cantidad': totales['cantidad_compras'],
        'total': totales['suma_total'],
        'proveedores': [
            {
                'id_proveedor': p['id_proveedor__id_proveedor'],
                'nombre': p['id_proveedor__nombre'],
                'cantidad_compras': p['cantidad_compras'],
                'total': p['total'],
            }
            for p in proveedores
        ],
        'insumos': [
            {
                'id_materia_prima': i['id_materia_prima__id_materia_prima'],
                'nombre': i['id_materia_prima__nombre'],
                'unidad_medida': i['id_materia_prima__unidad_medida'],
                'cantidad': i['cantidad'],
                'subtotal': i['subtotal'],
            }
            for i in insumos
        ],
    }
