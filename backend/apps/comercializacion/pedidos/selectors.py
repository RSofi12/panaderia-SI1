from django.shortcuts import get_object_or_404

from apps.comercializacion.pedidos.models import EstadoPedido, Pedido

ABIERTOS = (
    EstadoPedido.PENDIENTE,
    EstadoPedido.EN_PREPARACION,
    EstadoPedido.LISTO,
)


def _con_relaciones():
    return Pedido.objects.select_related('id_cliente', 'id_usuario', 'venta').prefetch_related(
        'detalles__id_producto',
    )


def obtener_pedido(pk):
    """Pedido con cliente, cajero y líneas."""
    return get_object_or_404(_con_relaciones(), pk=pk)


def listar_pedidos_abiertos():
    """Pedidos que Ventas todavía puede mover. La consulta de Producción es el CU15."""
    return _con_relaciones().filter(estado__in=ABIERTOS).order_by('fecha_entrega', 'id_pedido')
