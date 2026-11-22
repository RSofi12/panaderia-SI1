"""
Cobro del pedido antes de prepararlo (CU14).

El efectivo no llama a Stripe: el mostrador ya recibió el dinero.
La tarjeta solo queda pagada si Stripe confirma el PaymentIntent.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.comercializacion.pedidos.models import EstadoPedido, Pedido
from apps.comercializacion.ventas.models import MetodoPago
from apps.comercializacion.ventas.services.stripe_pago import (
    anular_cobro_tarjeta,
    confirmar_cobro_tarjeta,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

CERRADOS = {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO}


def pagar_pedido(*, usuario, pedido_id, agente_usuario=None, id_transaccion_stripe=None):
    referencia = (id_transaccion_stripe or '').strip() or None
    pedido = _pedido_cobrable(pedido_id)
    id_stripe = None
    if pedido.metodo_pago == MetodoPago.STRIPE:
        if not referencia:
            raise ValidationError({
                'id_transaccion_stripe': 'El pedido con tarjeta se paga con el id de Stripe.',
            })
        id_stripe = confirmar_cobro_tarjeta(id_transaccion_stripe=referencia, monto=pedido.total)
    elif referencia:
        raise ValidationError({
            'id_transaccion_stripe': 'Un pedido en efectivo no lleva cobro de tarjeta.',
        })

    try:
        with transaction.atomic():
            bloqueado = _pedido_cobrable(pedido_id, bloquear=True)
            if id_stripe:
                bloqueado.id_transaccion_stripe = id_stripe
            bloqueado.pagado = True
            bloqueado.save(update_fields=['pagado', 'id_transaccion_stripe'])
            Bitacora.registrar(
                usuario=usuario,
                accion=AccionBitacora.PAGO_PEDIDO,
                tabla_afectada='pedido',
                descripcion=(
                    f'Pedido {bloqueado.id_pedido} pagado en {bloqueado.metodo_pago} '
                    f'— total Bs {bloqueado.total}'
                ),
                agente_usuario=agente_usuario,
            )
            return bloqueado
    except Exception:
        if id_stripe:
            anular_cobro_tarjeta(id_stripe)
        raise


def _pedido_cobrable(pedido_id, bloquear=False):
    consulta = Pedido.objects.all()
    if bloquear:
        consulta = consulta.select_for_update()
    try:
        pedido = consulta.get(pk=pedido_id)
    except Pedido.DoesNotExist as exc:
        raise ValidationError({'pago': f'No existe el pedido {pedido_id}.'}) from exc
    if pedido.estado in CERRADOS:
        raise ValidationError({'pago': 'Un pedido entregado o cancelado ya no se puede pagar.'})
    if pedido.pagado:
        raise ValidationError({'pago': 'Este pedido ya está pagado.'})
    if pedido.metodo_pago not in (MetodoPago.EFECTIVO, MetodoPago.STRIPE):
        raise ValidationError({'metodo_pago': 'El pedido no tiene un método de pago.'})
    return pedido
