"""
Reporte dinámico de ventas (CU21).

Un mes es el rango desde el día 1 hasta el último, leído de venta.fecha_hora.
Esas filas ya las guardan el CU13 y la entrega del CU14. Este servicio no escribe.
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

    ventas = Venta.objects.filter(
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )
    if metodo_pago:
        ventas = ventas.filter(metodo_pago=metodo_pago)

    # El alias no puede llamarse "total": ese es el nombre del campo y Django
    # lo tomaría como el propio agregado.
    totales = ventas.aggregate(
        cantidad_ventas=Count('id_venta'),
        suma_total=Coalesce(Sum('total'), CERO),
        suma_efectivo=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.EFECTIVO)), CERO),
        suma_tarjeta=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.STRIPE)), CERO),
    )
    productos = (
        DetalleVenta.objects.filter(id_venta__in=ventas)
        .values('id_producto__nombre')
        .annotate(
            unidades=Coalesce(Sum('cantidad'), 0),
            importe=Coalesce(Sum('subtotal'), CERO),
        )
        .order_by('-importe', 'id_producto__nombre')
    )
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
    }
