"""
Registro de una venta de mostrador (CU13).

Efectivo: guarda la venta con id_transaccion_stripe vacío.
Stripe: el cobro ya fue confirmado; si el stock no alcanza, se anula en Stripe.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.comercializacion.ventas.services.stripe_pago import (
    anular_cobro_tarjeta,
    cobrar_con_tarjeta_manual,
    confirmar_cobro_tarjeta,
)
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado
from apps.productos_inventario.productos_terminados.services.descontar_stock import (
    descontar_por_venta,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def _validar_forma(detalles) -> list[dict]:
    if not detalles:
        raise ValidationError({'detalles': 'La venta debe incluir al menos un producto.'})

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
                    'No se puede repetir el mismo producto en una venta. '
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


def cotizar_detalles(detalles) -> tuple[list[dict], Decimal]:
    """
    Arma las líneas con el precio del catálogo.
    El total lo calcula el servidor; el navegador no lo envía.
    """
    forma = _validar_forma(detalles)
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
                'detalles': f'«{producto.nombre}» está inactivo y no se vende.'
            })
        if producto.precio_venta <= 0:
            raise ValidationError({
                'detalles': f'«{producto.nombre}» no tiene precio de venta.'
            })
        precio = Decimal(producto.precio_venta)
        subtotal = (precio * linea['cantidad']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total += subtotal
        lineas.append({
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'cantidad': linea['cantidad'],
            'precio': precio,
            'subtotal': subtotal,
        })
    return lineas, total


def _revisar_stock(lineas, inventarios) -> None:
    ids = [linea['id_producto'] for linea in lineas]
    if len(inventarios) != len(ids):
        sin_fila = sorted(set(ids) - set(inventarios))
        raise ValidationError({
            'detalles': f'Estos productos no tienen inventario de mostrador: {sin_fila}.'
        })

    faltantes = []
    for linea in lineas:
        inventario = inventarios[linea['id_producto']]
        if inventario.stock_actual < linea['cantidad']:
            faltantes.append(
                f'«{linea["nombre"]}»: hay {inventario.stock_actual} '
                f'y se piden {linea["cantidad"]}.'
            )
    if faltantes:
        raise ValidationError({'detalles': faltantes})


def asegurar_stock_disponible(lineas) -> None:
    """Lectura previa, sin bloqueo, para no cobrar en Stripe si ya no hay pan."""
    ids = [linea['id_producto'] for linea in lineas]
    inventarios = {
        inv.id_producto_id: inv
        for inv in InventarioProductoTerminado.objects.select_related('id_producto').filter(
            id_producto_id__in=ids
        )
    }
    _revisar_stock(lineas, inventarios)


def _siguiente_comprobante() -> int:
    ultima = (
        Venta.objects.select_for_update()
        .order_by('-numero_comprobante')
        .first()
    )
    if ultima is None:
        return 1
    return ultima.numero_comprobante + 1


@transaction.atomic
def _registrar_en_transaccion(*, usuario, metodo_pago, id_transaccion_stripe, detalles, total_esperado, agente_usuario):
    lineas, total = cotizar_detalles(detalles)
    if total != total_esperado:
        raise ValidationError({
            'total': 'El total cambió mientras se cobraba. La venta no se guardó.'
        })

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
    _revisar_stock(lineas, inventarios)

    venta = Venta.objects.create(
        id_usuario=usuario,
        numero_comprobante=_siguiente_comprobante(),
        metodo_pago=metodo_pago,
        id_transaccion_stripe=id_transaccion_stripe,
        total=Decimal('0'),
    )

    stock_resultante = []
    for linea in lineas:
        producto_id = linea['id_producto']
        inventario = inventarios[producto_id]
        DetalleVenta.objects.create(
            id_venta=venta,
            id_producto_id=producto_id,
            cantidad=linea['cantidad'],
            precio_unitario=linea['precio'],
            subtotal=linea['subtotal'],
        )
        descontar_por_venta(inventario=inventario, cantidad=linea['cantidad'], venta=venta)
        stock_resultante.append({
            'id_producto': producto_id,
            'nombre': linea['nombre'],
            'stock_actual': inventario.stock_actual,
        })

    venta.total = total
    venta.save(update_fields=['total'])
    venta.stock_resultante = stock_resultante

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.ALTA_VENTA,
        tabla_afectada='venta',
        descripcion=(
            f'Venta comprobante {venta.numero_comprobante} — {metodo_pago} — '
            f'total Bs {venta.total}'
        ),
        agente_usuario=agente_usuario,
    )
    return venta


def _anular_si_corresponde(id_stripe: str | None) -> None:
    if id_stripe:
        anular_cobro_tarjeta(id_stripe)


def registrar_venta(*, usuario, metodo_pago, id_transaccion_stripe=None, datos_tarjeta=None, detalles, agente_usuario=None):
    if metodo_pago not in MetodoPago.values:
        raise ValidationError({
            'metodo_pago': 'El método de pago debe ser efectivo o stripe.'
        })

    _, total = cotizar_detalles(detalles)
    # El stock se confirma dentro de la transacción, con la fila bloqueada.
    # Si Stripe ya cobró y el pan no alcanza, se anula ese cobro.

    id_stripe = None
    if metodo_pago == MetodoPago.STRIPE:
        if datos_tarjeta:
            id_stripe = cobrar_con_tarjeta_manual(monto=total, datos_tarjeta=datos_tarjeta)
        elif id_transaccion_stripe:
            id_stripe = confirmar_cobro_tarjeta(
                id_transaccion_stripe=id_transaccion_stripe,
                monto=total,
            )
        else:
            raise ValidationError({
                'tarjeta': 'La venta con Stripe requiere los datos de la tarjeta o el id de transacción.'
            })
    else:
        id_stripe = None

    for intento in range(2):
        try:
            return _registrar_en_transaccion(
                usuario=usuario,
                metodo_pago=metodo_pago,
                id_transaccion_stripe=id_stripe,
                detalles=detalles,
                total_esperado=total,
                agente_usuario=agente_usuario,
            )
        except ValidationError:
            _anular_si_corresponde(id_stripe)
            raise
        except IntegrityError as exc:
            texto = str(exc)
            if 'venta_id_transaccion_stripe_unica' in texto:
                raise ValidationError({
                    'id_transaccion_stripe': 'Este cobro de Stripe ya fue registrado.'
                }) from exc
            if intento == 1:
                _anular_si_corresponde(id_stripe)
                raise ValidationError({
                    'numero_comprobante': 'No se pudo asignar el comprobante. Intenta cobrar de nuevo.'
                }) from exc
    raise ValidationError({'numero_comprobante': 'No se pudo asignar el comprobante.'})
