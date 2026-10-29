"""
Cambio de estado del pedido (CU14).

Cancelar solo cambia el estado. Entregar, y solo desde listo, crea la venta.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.comercializacion.pedidos.models import EstadoPedido, Pedido
from apps.comercializacion.pedidos.services.entregar_pedido import entregar_pedido
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

TRANSICIONES = {
    EstadoPedido.PENDIENTE: {EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO},
    EstadoPedido.EN_PREPARACION: {EstadoPedido.LISTO, EstadoPedido.CANCELADO},
    EstadoPedido.LISTO: {EstadoPedido.CANCELADO},
}


def cambiar_estado_pedido(
    *,
    usuario,
    pedido_id,
    estado_nuevo,
    agente_usuario=None,
    datos_tarjeta=None,
    id_transaccion_stripe=None,
):
    with transaction.atomic():
        try:
            pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
        except Pedido.DoesNotExist as exc:
            raise ValidationError({'estado': f'No existe el pedido {pedido_id}.'}) from exc

        if estado_nuevo == EstadoPedido.ENTREGADO:
            return entregar_pedido(
                usuario=usuario,
                pedido=pedido,
                agente_usuario=agente_usuario,
                datos_tarjeta=datos_tarjeta,
                id_transaccion_stripe=id_transaccion_stripe,
            )

        permitidos = TRANSICIONES.get(pedido.estado, set())
        if estado_nuevo not in permitidos:
            raise ValidationError({
                'estado': f'No se puede pasar de {pedido.estado} a {estado_nuevo}.',
            })

        anterior = pedido.estado
        pedido.estado = estado_nuevo
        pedido.save(update_fields=['estado'])
        Bitacora.registrar(
            usuario=usuario,
            accion=AccionBitacora.CAMBIAR_ESTADO_PEDIDO,
            tabla_afectada='pedido',
            descripcion=f'Pedido {pedido.id_pedido}: {anterior} a {estado_nuevo}',
            agente_usuario=agente_usuario,
        )
    return pedido
