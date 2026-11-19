"""
Comando de poblado para Clientes y Pedidos (CU14).
Puebla los datos de clientes y pedidos anticipados según Poblacion_4_Dias_Panaderia_Santiago.sql.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.pedidos.models import Cliente, DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.models import MetodoPago
from apps.productos_inventario.productos.models import Producto

Usuario = get_user_model()

CLIENTES_DATA = [
    ('Rosa Fernández Choque', '70011122', 'Av. Banzer, 3er anillo'),
    ('Hotel Cortez', '33421100', 'Av. Cristo Redentor, 3er anillo'),
    ('Juan Pablo Áñez Rocha', '70055443', 'Calle Beni, casi 2do anillo'),
    ('Colegio San Ignacio', '33450099', 'Av. Alemana, 4to anillo'),
    ('Marcela Suárez Vaca', '70099887', 'Barrio Urbari, 2do anillo'),
    ('Restaurante El Aljibe', '33500221', 'Av. San Martín, 2do anillo'),
]

# (cliente_nombre, usuario_username, fecha_reg, fecha_entrega, estado, metodo_pago, transaccion_stripe, pagado, items)
# items: [(nombre_producto, cantidad, precio_unitario)]
PEDIDOS_DATA = [
    (
        'Rosa Fernández Choque',
        'mgonzales',
        datetime(2026, 9, 6, 8, 0),
        datetime(2026, 9, 6, 18, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Pan de Leche', 10, Decimal('1.25')), ('Pan Dulce', 10, Decimal('1.10'))],
    ),
    (
        'Hotel Cortez',
        'jrivera',
        datetime(2026, 9, 6, 9, 30),
        datetime(2026, 9, 7, 7, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.STRIPE,
        'pi_demo_pedido_2',
        True,
        [('Marraqueta', 100, Decimal('0.60')), ('Casero', 50, Decimal('0.70'))],
    ),
    (
        'Juan Pablo Áñez Rocha',
        'mgonzales',
        datetime(2026, 9, 6, 15, 0),
        datetime(2026, 9, 8, 9, 0),
        EstadoPedido.EN_PREPARACION,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Tortilla', 20, Decimal('1.75'))],
    ),
    (
        'Colegio San Ignacio',
        'jrivera',
        datetime(2026, 9, 6, 16, 20),
        datetime(2026, 9, 9, 7, 0),
        EstadoPedido.PENDIENTE,
        MetodoPago.STRIPE,
        None,
        False,
        [('Pan Mollete', 100, Decimal('0.60')), ('Pan Galleta', 100, Decimal('0.50'))],
    ),
    (
        'Marcela Suárez Vaca',
        'mgonzales',
        datetime(2026, 9, 7, 10, 0),
        datetime(2026, 9, 7, 19, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Pan con Azúcar', 15, Decimal('1.00')), ('Gusanito', 10, Decimal('1.50'))],
    ),
    (
        'Restaurante El Aljibe',
        'jrivera',
        datetime(2026, 9, 7, 11, 15),
        datetime(2026, 9, 8, 8, 0),
        EstadoPedido.LISTO,
        MetodoPago.STRIPE,
        'pi_demo_pedido_6',
        True,
        [('Chama', 30, Decimal('0.90')), ('Arani', 30, Decimal('0.80'))],
    ),
    (
        'Rosa Fernández Choque',
        'mgonzales',
        datetime(2026, 9, 7, 14, 45),
        datetime(2026, 9, 8, 17, 0),
        EstadoPedido.EN_PREPARACION,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Integral', 20, Decimal('0.90'))],
    ),
    (
        'Juan Pablo Áñez Rocha',
        'jrivera',
        datetime(2026, 9, 8, 8, 30),
        datetime(2026, 9, 8, 20, 0),
        EstadoPedido.PENDIENTE,
        MetodoPago.STRIPE,
        None,
        False,
        [('Pan de Leche', 15, Decimal('1.25'))],
    ),
    (
        'Marcela Suárez Vaca',
        'mgonzales',
        datetime(2026, 9, 8, 9, 45),
        datetime(2026, 9, 8, 12, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Marraqueta', 30, Decimal('0.60')), ('Pan Dulce', 10, Decimal('1.10'))],
    ),
    (
        'Hotel Cortez',
        'jrivera',
        datetime(2026, 9, 8, 10, 10),
        datetime(2026, 9, 9, 7, 0),
        EstadoPedido.CANCELADO,
        None,
        None,
        False,
        [('Casero', 50, Decimal('0.70'))],
    ),
]


class Command(BaseCommand):
    help = 'Puebla clientes y pedidos demo (CU14) según Poblacion_4_Dias_Panaderia_Santiago.sql'

    def handle(self, *args, **options):
        if Pedido.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {Pedido.objects.count()} pedidos registrados. No se aplicó el seed.'
                )
            )
            return

        usuarios = {u.nombre_usuario: u for u in Usuario.objects.all()}
        productos = {p.nombre: p for p in Producto.objects.all()}

        if not productos:
            self.stdout.write(
                self.style.ERROR('No hay productos en la base de datos. Ejecuta primero seed_productos.')
            )
            return

        usuario_default = Usuario.objects.filter(is_superuser=True).first() or Usuario.objects.first()

        with transaction.atomic():
            # 1. Clientes
            clientes = {}
            for nombre, tel, dir_ in CLIENTES_DATA:
                cliente, _ = Cliente.objects.get_or_create(
                    nombre=nombre,
                    defaults={'telefono': tel, 'direccion': dir_},
                )
                clientes[nombre] = cliente

            # 2. Pedidos y detalles
            creados = 0
            for cli_nom, usr_nom, f_reg, f_ent, est, met, st_id, pag, items in PEDIDOS_DATA:
                cliente = clientes.get(cli_nom)
                usuario = usuarios.get(usr_nom) or usuario_default

                total_calc = sum(cant * prec for _, cant, prec in items)

                pedido = Pedido.objects.create(
                    id_cliente=cliente,
                    id_usuario=usuario,
                    fecha_registro=timezone.make_aware(f_reg),
                    fecha_entrega=timezone.make_aware(f_ent) if f_ent else None,
                    estado=est,
                    metodo_pago=met,
                    id_transaccion_stripe=st_id,
                    pagado=pag,
                    total=total_calc,
                )

                for prod_nom, cant, prec in items:
                    prod = productos.get(prod_nom)
                    if prod:
                        DetallePedido.objects.create(
                            id_pedido=pedido,
                            id_producto=prod,
                            cantidad=cant,
                            precio_unitario=prec,
                            subtotal=cant * prec,
                        )

                creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Poblado de Pedidos completado: {len(clientes)} clientes y {creados} pedidos registrados.'
            )
        )
