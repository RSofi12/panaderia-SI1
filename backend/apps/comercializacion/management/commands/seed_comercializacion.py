"""Puebla datos demostrativos para consultar CU15 y CU17.

Uso:
    python manage.py seed_comercializacion

El comando es idempotente: los pedidos demostrativos se actualizan por cliente
y fecha, y sus líneas se reemplazan en cada ejecución. No crea ventas ni
descuenta inventario; CU15 es una consulta y CU17 lee las existencias creadas
por ``seed_existencias``.
"""
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.pedidos.models import Cliente, DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.models import MetodoPago
from apps.productos_inventario.productos.models import Producto
from apps.usuarios_seguridad.users.models import Usuario


PEDIDOS_DEMO = [
    ('Hotel Cortez', '2026-09-06T18:00:00', EstadoPedido.ENTREGADO, MetodoPago.EFECTIVO,
     [('Pan de Leche', 10), ('Pan Dulce', 10)]),
    ('Café Central', '2026-09-07T07:00:00', EstadoPedido.ENTREGADO, MetodoPago.STRIPE,
     [('Marraqueta', 100), ('Casero', 50)]),
    ('Restaurante La Sierra', '2026-09-08T09:00:00', EstadoPedido.EN_PREPARACION, MetodoPago.EFECTIVO,
     [('Tortilla', 20)]),
    ('Eventos Oriente', '2026-09-09T07:00:00', EstadoPedido.PENDIENTE, MetodoPago.STRIPE,
     [('Pan Mollete', 100), ('Pan Galleta', 100)]),
    ('Colegio San Marcos', '2026-09-07T19:00:00', EstadoPedido.ENTREGADO, MetodoPago.EFECTIVO,
     [('Pan con Azúcar', 15), ('Gusanito', 10)]),
    ('Café Plaza', '2026-09-08T08:00:00', EstadoPedido.LISTO, MetodoPago.STRIPE,
     [('Chama', 30), ('Arani', 30)]),
    ('Hotel Los Tajibos', '2026-09-08T17:00:00', EstadoPedido.EN_PREPARACION, MetodoPago.EFECTIVO,
     [('Integral', 20)]),
    ('Supermercado Norte', '2026-09-08T20:00:00', EstadoPedido.PENDIENTE, MetodoPago.STRIPE,
     [('Pan de Leche', 15)]),
    ('Restaurante El Patio', '2026-09-08T12:00:00', EstadoPedido.ENTREGADO, MetodoPago.EFECTIVO,
     [('Marraqueta', 30), ('Pan Dulce', 10)]),
    ('Panadería Vecina', '2026-09-09T07:00:00', EstadoPedido.CANCELADO, None,
     [('Casero', 50)]),
]


class Command(BaseCommand):
    help = 'Puebla pedidos demostrativos para CU15 y prepara datos visibles para CU17.'

    def handle(self, *args, **options):
        try:
            usuario_ventas = Usuario.objects.get(nombre_usuario='mgonzales', activo=True)
            usuario_produccion = Usuario.objects.get(nombre_usuario='mrojas', activo=True)
        except Usuario.DoesNotExist as exc:
            raise CommandError('Ejecuta primero: python manage.py seed_usuarios') from exc

        nombres_productos = {nombre for _, _, _, _, lineas in PEDIDOS_DEMO for nombre, _ in lineas}
        productos = {
            producto.nombre: producto
            for producto in Producto.objects.filter(nombre__in=nombres_productos)
        }
        faltantes = sorted(nombres_productos - set(productos))
        if faltantes:
            raise CommandError(
                f'Faltan productos {faltantes}. Ejecuta primero: python manage.py seed_productos'
            )

        with transaction.atomic():
            pedidos_creados = 0
            pedidos_actualizados = 0
            for indice, (nombre_cliente, fecha, estado, metodo_pago, lineas) in enumerate(PEDIDOS_DEMO):
                cliente, _ = Cliente.objects.get_or_create(nombre=nombre_cliente)
                fecha_registro = timezone.make_aware(datetime.fromisoformat(fecha))
                pedido, creado = Pedido.objects.update_or_create(
                    id_cliente=cliente,
                    fecha_registro=fecha_registro,
                    defaults={
                        'id_usuario': usuario_ventas if indice % 2 == 0 else usuario_produccion,
                        'fecha_entrega': fecha_registro,
                        'estado': estado,
                        'metodo_pago': metodo_pago,
                    },
                )
                pedido.detalles.all().delete()
                total = Decimal('0.00')
                detalles = []
                for nombre_producto, cantidad in lineas:
                    producto = productos[nombre_producto]
                    precio = Decimal(producto.precio_venta).quantize(Decimal('0.01'))
                    subtotal = (precio * cantidad).quantize(Decimal('0.01'))
                    total += subtotal
                    detalles.append(DetallePedido(
                        id_pedido=pedido,
                        id_producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                    ))
                DetallePedido.objects.bulk_create(detalles)
                pedido.total = total
                pedido.save(update_fields=['total'])
                if creado:
                    pedidos_creados += 1
                else:
                    pedidos_actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'CU15 poblado: {pedidos_creados} pedidos creados, {pedidos_actualizados} actualizados. '
            'Para CU17 ejecuta también: python manage.py seed_existencias'
        ))
