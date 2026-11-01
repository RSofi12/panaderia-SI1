"""
Alta de un pedido anticipado (CU14).

El pedido nace en pendiente. El precio sale del catálogo.
No cobra, no crea una venta y no descuenta stock.
"""
from datetime import time
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.pedidos.models import (
    Cliente,
    DetallePedido,
    EstadoPedido,
    Pedido,
)
from apps.comercializacion.ventas.models import MetodoPago
from apps.comercializacion.ventas.services.stripe_pago import (
    anular_cobro_tarjeta,
    confirmar_cobro_tarjeta,
    crear_intencion,
)
from apps.productos_inventario.productos.models import Producto
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

CENTAVO = Decimal('0.01')
APERTURA = time(8, 0)
CIERRE = time(17, 0)


def preparar_cobro_tarjeta(*, detalles):
    """Arma el PaymentIntent del carrito. Todavía no existe el pedido."""
    forma = _validar_forma(detalles)
    _, total = _cotizar(forma)
    return crear_intencion(monto=total, origen='cu14-pedido')


def registrar_pedido(
    *,
    usuario,
    cliente,
    fecha_entrega,
    metodo_pago,
    detalles,
    agente_usuario=None,
    id_transaccion_stripe=None,
):
    fecha_entrega = _validar_fecha_entrega(fecha_entrega)
    if metodo_pago not in (MetodoPago.EFECTIVO, MetodoPago.STRIPE):
        raise ValidationError({'metodo_pago': 'El método debe ser efectivo o stripe.'})

    forma = _validar_forma(detalles)
    lineas, total = _cotizar(forma)
    referencia = (id_transaccion_stripe or '').strip() or None
    if metodo_pago == MetodoPago.EFECTIVO and referencia:
        raise ValidationError({
            'id_transaccion_stripe': 'Un pedido en efectivo no lleva cobro de tarjeta.',
        })
    id_stripe = None
    if referencia:
        id_stripe = confirmar_cobro_tarjeta(id_transaccion_stripe=referencia, monto=total)
    try:
        return _guardar_pedido(
            usuario=usuario,
            cliente=cliente,
            fecha_entrega=fecha_entrega,
            metodo_pago=metodo_pago,
            lineas=lineas,
            total=total,
            id_stripe=id_stripe,
            agente_usuario=agente_usuario,
        )
    except Exception:
        if id_stripe:
            anular_cobro_tarjeta(id_stripe)
        raise


def _guardar_pedido(
    *,
    usuario,
    cliente,
    fecha_entrega,
    metodo_pago,
    lineas,
    total,
    id_stripe,
    agente_usuario,
):
    with transaction.atomic():
        cliente_guardado = _resolver_cliente(cliente)
        pedido = Pedido.objects.create(
            id_cliente=cliente_guardado,
            id_usuario=usuario,
            fecha_entrega=fecha_entrega,
            estado=EstadoPedido.PENDIENTE,
            metodo_pago=metodo_pago,
            id_transaccion_stripe=id_stripe,
            total=total,
        )
        DetallePedido.objects.bulk_create([
            DetallePedido(
                id_pedido=pedido,
                id_producto_id=linea['id_producto'],
                cantidad=linea['cantidad'],
                precio_unitario=linea['precio'],
                subtotal=linea['subtotal'],
            )
            for linea in lineas
        ])
        Bitacora.registrar(
            usuario=usuario,
            accion=AccionBitacora.ALTA_PEDIDO,
            tabla_afectada='pedido',
            descripcion=(
                f'Pedido {pedido.id_pedido} — {cliente_guardado.nombre} — '
                f'entrega {fecha_entrega:%Y-%m-%d %H:%M} — {metodo_pago} — '
                f'total Bs {total}'
            ),
            agente_usuario=agente_usuario,
        )
    return pedido


def _validar_fecha_entrega(fecha_entrega):
    """La entrega es hoy o después, y solo dentro del horario de la panadería."""
    if fecha_entrega is None:
        raise ValidationError({'fecha_entrega': 'Indica la fecha de entrega prevista.'})
    if timezone.is_naive(fecha_entrega):
        fecha_entrega = timezone.make_aware(fecha_entrega, timezone.get_current_timezone())
    local = timezone.localtime(fecha_entrega)
    ahora = timezone.localtime()
    if local.date() < ahora.date():
        raise ValidationError({
            'fecha_entrega': 'La entrega no puede ser en una fecha anterior a hoy.',
        })
    if not (APERTURA <= local.time() <= CIERRE):
        raise ValidationError({
            'fecha_entrega': 'El horario para retirar es de 08:00 a 17:00.',
        })
    if local <= ahora:
        raise ValidationError({
            'fecha_entrega': 'Esa hora de hoy ya pasó. Elige una hora más tarde u otro día.',
        })
    return local


def _resolver_cliente(cliente: dict) -> Cliente:
    id_cliente = cliente.get('id_cliente')
    if id_cliente:
        encontrado = Cliente.objects.filter(pk=id_cliente).first()
        if encontrado is None:
            raise ValidationError({'cliente': f'No existe el cliente {id_cliente}.'})
        return encontrado

    nombre = (cliente.get('nombre') or '').strip()
    if not nombre:
        raise ValidationError({'cliente': 'Indica un cliente existente o el nombre de uno nuevo.'})
    return Cliente.objects.create(
        nombre=nombre,
        telefono=(cliente.get('telefono') or '').strip() or None,
        direccion=(cliente.get('direccion') or '').strip() or None,
    )


def _validar_forma(detalles) -> list[dict]:
    if not detalles:
        raise ValidationError({'detalles': 'El pedido debe incluir al menos un producto.'})

    normalizados = []
    vistos: set[int] = set()
    for indice, raw in enumerate(detalles, start=1):
        if not isinstance(raw, dict):
            raise ValidationError({'detalles': f'El detalle #{indice} no tiene formato válido.'})
        try:
            id_producto = int(raw['id_producto'])
            cantidad = int(raw['cantidad'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError({
                'detalles': f'El detalle #{indice} debe indicar id_producto y cantidad entera.'
            }) from exc
        if id_producto in vistos:
            raise ValidationError({
                'detalles': (
                    'No se puede repetir el mismo producto en un pedido. '
                    'Suma la cantidad en una sola línea.'
                )
            })
        vistos.add(id_producto)
        if cantidad <= 0:
            raise ValidationError({
                'detalles': f'El detalle #{indice}: la cantidad debe ser mayor a cero.'
            })
        normalizados.append({'id_producto': id_producto, 'cantidad': cantidad})
    return normalizados


def _cotizar(forma: list[dict]) -> tuple[list[dict], Decimal]:
    ids = [linea['id_producto'] for linea in forma]
    productos = Producto.objects.in_bulk(ids)
    if len(productos) != len(ids):
        faltantes = sorted(set(ids) - set(productos))
        raise ValidationError({'detalles': f'Producto(s) no encontrado(s): {faltantes}.'})

    lineas = []
    total = Decimal('0')
    for linea in forma:
        producto = productos[linea['id_producto']]
        if not producto.activo:
            raise ValidationError({
                'detalles': f'«{producto.nombre}» está inactivo y no se puede pedir.'
            })
        if producto.precio_venta <= 0:
            raise ValidationError({
                'detalles': f'«{producto.nombre}» no tiene precio de venta.'
            })
        precio = Decimal(producto.precio_venta).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        subtotal = (precio * linea['cantidad']).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        total += subtotal
        lineas.append({
            'id_producto': producto.id_producto,
            'cantidad': linea['cantidad'],
            'precio': precio,
            'subtotal': subtotal,
        })
    return lineas, total.quantize(CENTAVO, rounding=ROUND_HALF_UP)
