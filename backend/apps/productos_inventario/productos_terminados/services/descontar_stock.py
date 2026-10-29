"""
Único lugar que resta stock de producto terminado por una venta (CU13).

CU18 (mermas) debe reutilizar esta misma idea: la venta no actualiza
inventario por su cuenta.
"""
from django.core.exceptions import ValidationError

from apps.productos_inventario.productos_terminados.models import (
    MovimientoProductoTerminado,
    TipoMovimientoProductoTerminado,
)


def descontar_por_venta(*, inventario, cantidad: int, venta, pedido=None) -> None:
    """
    Resta unidades y deja la salida en el kardex.
    Se llama dentro de la transacción de la venta, con la fila ya bloqueada.
    """
    if cantidad <= 0:
        raise ValidationError({'detalles': 'La cantidad debe ser mayor a cero.'})

    if inventario.stock_actual < cantidad:
        nombre = inventario.id_producto.nombre
        raise ValidationError({
            'detalles': (
                f'Sin stock de «{nombre}»: hay {inventario.stock_actual} '
                f'y se piden {cantidad}.'
            )
        })

    inventario.stock_actual -= cantidad
    inventario.save(update_fields=['stock_actual'])

    MovimientoProductoTerminado.objects.create(
        id_inventario=inventario,
        id_venta=venta,
        id_pedido=pedido,
        tipo=TipoMovimientoProductoTerminado.SALIDA,
        cantidad=cantidad,
    )
