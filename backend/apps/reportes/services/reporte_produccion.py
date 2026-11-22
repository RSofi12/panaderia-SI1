"""
Reporte dinámico de producción (CU22).

Agrega jornadas y unidades horneadas en un período, y las compara con las
unidades vendidas del mismo rango de fechas. Solo lectura (OLAP): no altera
producción, inventario ni ventas.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.comercializacion.ventas.models import DetalleVenta
from apps.productos_inventario.produccion.models import JornadaProduccion, Produccion
from apps.productos_inventario.productos.models import Producto

CERO = Decimal('0.00')
JORNADAS_VALIDAS = frozenset(JornadaProduccion.values)


def _responsable(usuario) -> str:
    if not usuario:
        return 'Sistema'
    return usuario.nombre_completo or usuario.nombre_usuario


def reporte_produccion(*, desde: date, hasta: date, jornada=None) -> dict:
    """Totales, lotes y comparativa producción vs ventas del período."""
    if desde > hasta:
        raise ValidationError({'hasta': 'La fecha final no puede ser anterior a la inicial.'})
    if jornada not in (None, '', *JORNADAS_VALIDAS):
        raise ValidationError({'jornada': 'La jornada debe ser Mañana, Tarde, Noche o unica.'})

    lotes_qs = (
        Produccion.objects.filter(fecha__gte=desde, fecha__lte=hasta)
        .select_related('id_usuario')
        .prefetch_related('detalles')
        .order_by('-fecha', '-id_produccion')
    )
    if jornada:
        lotes_qs = lotes_qs.filter(jornada=jornada)

    unidades = 0
    costo = CERO
    por_jornada = {
        JornadaProduccion.MANANA: 0,
        JornadaProduccion.TARDE: 0,
        JornadaProduccion.NOCHE: 0,
        JornadaProduccion.UNICA: 0,
    }
    producidas: dict[int, dict] = {}
    lotes = []
    ids_producto: set[int] = set()

    for produccion in lotes_qs:
        detalles = list(produccion.detalles.all())
        panes = sum(detalle.cantidad_producida for detalle in detalles)
        costo_lote = sum(
            (Decimal(detalle.cantidad_producida) * detalle.costo_unitario for detalle in detalles),
            CERO,
        ).quantize(Decimal('0.01'))
        unidades += panes
        costo += costo_lote
        por_jornada[produccion.jornada] = por_jornada.get(produccion.jornada, 0) + panes

        for detalle in detalles:
            producto_id = detalle.id_producto_id
            ids_producto.add(producto_id)
            fila = producidas.setdefault(
                producto_id,
                {
                    'cantidad': 0,
                    'costo': CERO,
                },
            )
            fila['cantidad'] += detalle.cantidad_producida
            fila['costo'] += Decimal(detalle.cantidad_producida) * detalle.costo_unitario

        lotes.append(
            {
                'id_produccion': produccion.id_produccion,
                'fecha': produccion.fecha.isoformat(),
                'jornada': produccion.get_jornada_display(),
                'jornada_codigo': produccion.jornada,
                'responsable': _responsable(produccion.id_usuario),
                'unidades': panes,
                'variedades': len(detalles),
                'costo': costo_lote,
            }
        )

    vendidas_qs = (
        DetalleVenta.objects.filter(
            id_venta__fecha_hora__date__gte=desde,
            id_venta__fecha_hora__date__lte=hasta,
        )
        .values('id_producto')
        .annotate(vendidas=Coalesce(Sum('cantidad'), 0))
    )
    vendidas_por_producto = {fila['id_producto']: int(fila['vendidas']) for fila in vendidas_qs}
    unidades_vendidas = sum(vendidas_por_producto.values())
    ids_producto.update(vendidas_por_producto)

    for producto_id in vendidas_por_producto:
        producidas.setdefault(producto_id, {'cantidad': 0, 'costo': CERO})

    nombres = dict(
        Producto.objects.filter(pk__in=ids_producto).values_list('id_producto', 'nombre')
    )

    productos = []
    for producto_id, fila in producidas.items():
        vendidas = vendidas_por_producto.get(producto_id, 0)
        productos.append(
            {
                'nombre': nombres.get(producto_id, f'Producto #{producto_id}'),
                'cantidad': fila['cantidad'],
                'vendidas': vendidas,
                'diferencia': fila['cantidad'] - vendidas,
                'costo': fila['costo'].quantize(Decimal('0.01')),
            }
        )
    productos.sort(key=lambda item: (-item['cantidad'], -item['vendidas'], item['nombre']))

    return {
        'desde': desde,
        'hasta': hasta,
        'cantidad': len(lotes),
        'unidades': unidades,
        'unidades_vendidas': unidades_vendidas,
        'diferencia': unidades - unidades_vendidas,
        'costo': costo.quantize(Decimal('0.01')),
        'manana': por_jornada.get(JornadaProduccion.MANANA, 0),
        'tarde': por_jornada.get(JornadaProduccion.TARDE, 0),
        'noche': por_jornada.get(JornadaProduccion.NOCHE, 0),
        'lotes': lotes,
        'productos': productos,
    }
