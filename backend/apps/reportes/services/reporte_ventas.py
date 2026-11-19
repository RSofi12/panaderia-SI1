"""
Reporte dinámico de ventas (CU21).

Calcula en tiempo real totales agregados, desglose por producto y detalle
de ventas individuales a partir de las tablas transaccionales Venta y DetalleVenta.
Este servicio es de solo lectura (OLAP).
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta

CERO = Decimal('0.00')


def reporte_ventas(*, desde: date, hasta: date, metodo_pago=None) -> dict:
    if desde > hasta:
        raise ValidationError({'hasta': 'La fecha final no puede ser anterior a la inicial.'})
    if metodo_pago not in (None, '', MetodoPago.EFECTIVO, MetodoPago.STRIPE):
        raise ValidationError({'metodo_pago': 'El método debe ser efectivo o stripe.'})

    ventas_qs = Venta.objects.filter(
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )
    if metodo_pago:
        ventas_qs = ventas_qs.filter(metodo_pago=metodo_pago)

    # 1. Totales generales agregados
    totales = ventas_qs.aggregate(
        cantidad_ventas=Count('id_venta'),
        suma_total=Coalesce(Sum('total'), CERO),
        suma_efectivo=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.EFECTIVO)), CERO),
        suma_tarjeta=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.STRIPE)), CERO),
    )

    # 2. Desglose de productos vendidos
    productos = (
        DetalleVenta.objects.filter(id_venta__in=ventas_qs)
        .values('id_producto__nombre')
        .annotate(
            unidades=Coalesce(Sum('cantidad'), 0),
            importe=Coalesce(Sum('subtotal'), CERO),
        )
        .order_by('-importe', 'id_producto__nombre')
    )

    # 3. Listado detallado de transacciones individuales de ventas
    ventas_lista = [
        {
            'id_venta': v.id_venta,
            'numero_comprobante': v.numero_comprobante,
            'fecha': v.fecha_hora.strftime('%Y-%m-%d'),
            'fecha_hora': v.fecha_hora.strftime('%Y-%m-%d %H:%M'),
            'metodo_pago': v.metodo_pago,
            'total': v.total,
            'cajero': (v.id_usuario.nombre_completo or v.id_usuario.nombre_usuario) if v.id_usuario else 'Sistema',
        }
        for v in ventas_qs.select_related('id_usuario').order_by('-fecha_hora', '-id_venta')
    ]

    return {
        'desde': desde,
        'hasta': hasta,
        'cantidad': totales['cantidad_ventas'],
        'total': totales['suma_total'],
        'efectivo': totales['suma_efectivo'],
        'tarjeta': totales['suma_tarjeta'],
        'productos': [
            {
                'nombre': fila['id_producto__nombre'],
                'cantidad': fila['unidades'],
                'subtotal': fila['importe'],
            }
            for fila in productos
        ],
        'ventas': ventas_lista,
    }
