"""
Servicio transaccional para CU18: Registrar baja de productos terminados (perdidas/mermas).
Descuenta unidades del inventario de producto terminado, registra el movimiento de salida
en el kardex y crea la NotaPerdidaProducto auditada en Bitacora (CU26).
"""
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.produccion.models import DetalleProduccion
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
    TipoMovimientoProductoTerminado,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def registrar_baja_producto(
    *,
    id_producto: int,
    cantidad: int,
    usuario,
    id_detalle_produccion: Optional[int] = None,
    motivo: str = 'Merma / Producto defectuoso',
    observaciones: str = '',
    costo_unitario: Optional[Decimal] = None,
    fecha_salida=None,
    agente_usuario: Optional[str] = None,
) -> NotaPerdidaProducto:
    if cantidad <= 0:
        raise ValidationError({'cantidad': 'La cantidad de baja debe ser un numero entero mayor a 0.'})

    if not fecha_salida:
        fecha_salida = timezone.now()

    with transaction.atomic():
        try:
            producto = Producto.objects.select_related('id_categoria').get(id_producto=id_producto)
        except Producto.DoesNotExist:
            raise ValidationError({'id_producto': f'No existe el producto con ID {id_producto}.'})

        try:
            inventario = (
                InventarioProductoTerminado.objects.select_for_update()
                .select_related('id_producto')
                .get(id_producto=producto)
            )
        except InventarioProductoTerminado.DoesNotExist:
            raise ValidationError({
                'id_producto': f'El producto "{producto.nombre}" no tiene inventario inicializado.'
            })

        if inventario.stock_actual < cantidad:
            raise ValidationError({
                'cantidad': (
                    f'Stock insuficiente para "{producto.nombre}": actualmente hay '
                    f'{inventario.stock_actual} unidades en vitrina y se intenta dar de baja {cantidad}.'
                )
            })

        detalle_prod = None
        if id_detalle_produccion:
            try:
                detalle_prod = DetalleProduccion.objects.select_related('id_producto', 'id_produccion').get(
                    id_detalle_produccion=id_detalle_produccion,
                    id_producto=producto,
                )
            except DetalleProduccion.DoesNotExist:
                raise ValidationError({
                    'id_detalle_produccion': (
                        f'El detalle de produccion #{id_detalle_produccion} no corresponde al producto "{producto.nombre}".'
                    )
                })
        else:
            detalle_prod = (
                DetalleProduccion.objects.filter(id_producto=producto)
                .order_by('-id_detalle_produccion')
                .first()
            )

        if not detalle_prod:
            from apps.productos_inventario.produccion.models import Produccion, JornadaProduccion
            prod_base, _ = Produccion.objects.get_or_create(
                jornada=JornadaProduccion.UNICA,
                defaults={
                    'id_usuario': usuario,
                    'fecha': timezone.now().date(),
                }
            )
            costo_base = producto.costo_produccion or Decimal('0.00')
            detalle_prod, _ = DetalleProduccion.objects.get_or_create(
                id_produccion=prod_base,
                id_producto=producto,
                defaults={
                    'cantidad_producida': cantidad,
                    'costo_unitario': costo_base,
                }
            )

        if costo_unitario is None:
            costo_unitario = detalle_prod.costo_unitario or producto.costo_produccion or Decimal('0.00')
        costo_unitario = Decimal(str(costo_unitario)).quantize(Decimal('0.01'))
        costo_total = (Decimal(cantidad) * costo_unitario).quantize(Decimal('0.01'))

        # Descontar stock
        inventario.stock_actual -= cantidad
        inventario.save(update_fields=['stock_actual'])

        # Crear NotaPerdidaProducto
        nota = NotaPerdidaProducto.objects.create(
            id_detalle_produccion=detalle_prod,
            id_usuario=usuario,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            fecha_salida=fecha_salida,
        )

        # Registrar en Kardex
        MovimientoProductoTerminado.objects.create(
            id_inventario=inventario,
            id_nota_perdida=nota,
            id_produccion=detalle_prod.id_produccion,
            tipo=TipoMovimientoProductoTerminado.SALIDA,
            cantidad=cantidad,
            fecha_hora=fecha_salida,
        )

        # Auditar en Bitacora (CU26)
        desc = (
            f"Baja/merma de {cantidad} un. de '{producto.nombre}' | "
            f"Motivo: {motivo} | Costo unitario: Bs {costo_unitario} | Total perdida: Bs {costo_total}"
        )
        if observaciones:
            desc += f" | Obs: {observaciones.strip()}"

        Bitacora.registrar(
            usuario=usuario,
            accion=AccionBitacora.REGISTRO_BAJA_PRODUCTO,
            tabla_afectada='nota_perdida_producto',
            descripcion=desc,
            agente_usuario=agente_usuario,
        )

        return nota