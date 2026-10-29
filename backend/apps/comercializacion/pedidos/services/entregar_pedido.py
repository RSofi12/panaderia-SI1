"""
Entrega de un pedido listo (CU14).

Crea una sola venta con el precio congelado en el detalle del pedido,
la enlaza con venta.id_pedido y descuenta el stock con la misma función
del mostrador. El efectivo no llama a Stripe. La tarjeta se cobra aquí.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.comercializacion.pedidos.models import DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.comercializacion.ventas.services.registrar_venta import _siguiente_comprobante
from apps.comercializacion.ventas.services.stripe_pago import (
    anular_cobro_tarjeta,
    cobrar_con_tarjeta_manual,
    confirmar_cobro_tarjeta,
)
from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado
from apps.productos_inventario.productos_terminados.services.descontar_stock import (
    descontar_por_venta,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def entregar_pedido(
    *,
    usuario,
    pedido: Pedido,
    agente_usuario=None,
    datos_tarjeta=None,
    id_transaccion_stripe=None,
):
    if pedido.estado != EstadoPedido.LISTO:
        raise ValidationError({
            'estado': f'No se puede pasar de {pedido.estado} a entregado.',
        })
    if pedido.metodo_pago not in (MetodoPago.EFECTIVO, MetodoPago.STRIPE):
        raise ValidationError({'metodo_pago': 'El pedido no tiene un método de pago previsto.'})

    lineas = _lineas_congeladas(pedido)
    total = sum((linea['subtotal'] for linea in lineas), Decimal('0'))
    id_stripe = None
    try:
        id_stripe = _cobrar(
            metodo=pedido.metodo_pago,
            total=total,
            datos_tarjeta=datos_tarjeta,
            id_transaccion_stripe=id_transaccion_stripe,
        )
        for intento in range(2):
            try:
                with transaction.atomic():
                    return _guardar(
                        usuario=usuario,
                        pedido=pedido,
                        lineas=lineas,
                        total=total,
                        id_stripe=id_stripe,
                        agente_usuario=agente_usuario,
                    )
            except IntegrityError as exc:
                if intento == 1 or 'venta_id_transaccion_stripe_unica' in str(exc):
                    raise ValidationError({
                        'numero_comprobante': 'No se pudo registrar la venta de la entrega.',
                    }) from exc
    except ValidationError:
        if id_stripe:
            anular_cobro_tarjeta(id_stripe)
        raise
    raise ValidationError({'numero_comprobante': 'No se pudo registrar la venta de la entrega.'})


def _lineas_congeladas(pedido: Pedido) -> list[dict]:
    detalles = DetallePedido.objects.select_related('id_producto').filter(id_pedido=pedido)
    lineas = []
    for detalle in detalles:
        lineas.append({
            'id_producto': detalle.id_producto_id,
            'nombre': detalle.id_producto.nombre,
            'cantidad': detalle.cantidad,
            'precio': detalle.precio_unitario,
            'subtotal': detalle.subtotal,
        })
    if not lineas:
        raise ValidationError({'detalles': 'El pedido no tiene productos para entregar.'})
    return lineas


def _cobrar(*, metodo, total, datos_tarjeta, id_transaccion_stripe):
    referencia = (id_transaccion_stripe or '').strip()
    if metodo == MetodoPago.EFECTIVO:
        if datos_tarjeta or referencia:
            raise ValidationError({
                'id_transaccion_stripe': 'Una entrega en efectivo no lleva datos de tarjeta.',
            })
        return None
    if datos_tarjeta:
        return cobrar_con_tarjeta_manual(monto=total, datos_tarjeta=datos_tarjeta)
    if referencia:
        return confirmar_cobro_tarjeta(id_transaccion_stripe=referencia, monto=total)
    raise ValidationError({
        'tarjeta': 'La entrega con tarjeta requiere los datos de la tarjeta o el id de transacción.',
    })


def _guardar(*, usuario, pedido, lineas, total, id_stripe, agente_usuario):
    ids = [linea['id_producto'] for linea in lineas]
    inventarios = {
        inv.id_producto_id: inv
        for inv in (
            InventarioProductoTerminado.objects.select_for_update()
            .filter(id_producto_id__in=ids)
            .select_related('id_producto')
            .order_by('id_producto_id')
        )
    }
    if len(inventarios) != len(ids):
        sin_fila = sorted(set(ids) - set(inventarios))
        raise ValidationError({
            'detalles': f'Estos productos no tienen inventario de mostrador: {sin_fila}.',
        })

    venta = Venta.objects.create(
        id_pedido=pedido,
        id_usuario=usuario,
        numero_comprobante=_siguiente_comprobante(),
        metodo_pago=pedido.metodo_pago,
        id_transaccion_stripe=id_stripe,
        total=total,
    )
    for linea in lineas:
        inventario = inventarios[linea['id_producto']]
        DetalleVenta.objects.create(
            id_venta=venta,
            id_producto_id=linea['id_producto'],
            cantidad=linea['cantidad'],
            precio_unitario=linea['precio'],
            subtotal=linea['subtotal'],
        )
        descontar_por_venta(
            inventario=inventario,
            cantidad=linea['cantidad'],
            venta=venta,
            pedido=pedido,
        )

    pedido.estado = EstadoPedido.ENTREGADO
    pedido.save(update_fields=['estado'])
    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.CAMBIAR_ESTADO_PEDIDO,
        tabla_afectada='pedido',
        descripcion=f'Pedido {pedido.id_pedido}: listo a entregado — comprobante {venta.numero_comprobante}',
        agente_usuario=agente_usuario,
    )
    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.ALTA_VENTA,
        tabla_afectada='venta',
        descripcion=(
            f'Venta comprobante {venta.numero_comprobante} por pedido {pedido.id_pedido} — '
            f'{pedido.metodo_pago} — total Bs {total}'
        ),
        agente_usuario=agente_usuario,
    )
    return pedido
