"""
Comando de poblado para Clientes y Pedidos (CU14).
Puebla los datos de clientes y pedidos anticipados:
- Base histórica de Septiembre según Poblacion_4_Dias_Panaderia_Santiago.sql.
- Pedidos institucionales recientes de Noviembre 2026 (hoteles, colegios, restaurantes).
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.pedidos.models import Cliente, DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.models import MetodoPago, Venta
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import MovimientoProductoTerminado

Usuario = get_user_model()

CLIENTES_DATA = [
    ('Rosa Fernández Choque', '70011122', 'Av. Banzer, 3er anillo'),
    ('Hotel Cortez', '33421100', 'Av. Cristo Redentor, 3er anillo'),
    ('Juan Pablo Áñez Rocha', '70055443', 'Calle Beni, casi 2do anillo'),
    ('Colegio San Ignacio', '33450099', 'Av. Alemana, 4to anillo'),
    ('Marcela Suárez Vaca', '70099887', 'Barrio Urbari, 2do anillo'),
    ('Restaurante El Aljibe', '33500221', 'Av. San Martín, 2do anillo'),
]

# Pedidos de Septiembre (Histórico base)
PEDIDOS_SEPTIEMBRE = [
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

# Pedidos institucionales de Noviembre 2026
PEDIDOS_NOVIEMBRE = [
    (
        'Hotel Cortez',
        'mgonzales',
        datetime(2026, 11, 2, 8, 30),
        datetime(2026, 11, 3, 7, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.STRIPE,
        'pi_ped_nov_01',
        True,
        [('Marraqueta', 120, Decimal('0.60')), ('Casero', 60, Decimal('0.70')), ('Pan de Leche', 40, Decimal('1.25'))],
    ),
    (
        'Colegio San Ignacio',
        'jrivera',
        datetime(2026, 11, 4, 15, 0),
        datetime(2026, 11, 5, 8, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Pan Mollete', 100, Decimal('0.60')), ('Pan Galleta', 100, Decimal('0.50')), ('Pan Dulce', 50, Decimal('1.10'))],
    ),
    (
        'Restaurante El Aljibe',
        'mgonzales',
        datetime(2026, 11, 6, 9, 15),
        datetime(2026, 11, 6, 17, 30),
        EstadoPedido.ENTREGADO,
        MetodoPago.STRIPE,
        'pi_ped_nov_02',
        True,
        [('Arani', 50, Decimal('0.80')), ('Chama', 50, Decimal('0.90')), ('Tortilla', 20, Decimal('1.75'))],
    ),
    (
        'Rosa Fernández Choque',
        'jrivera',
        datetime(2026, 11, 9, 16, 20),
        datetime(2026, 11, 10, 18, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Integral', 30, Decimal('0.90')), ('Pan de Leche', 20, Decimal('1.25'))],
    ),
    (
        'Hotel Cortez',
        'mgonzales',
        datetime(2026, 11, 11, 8, 0),
        datetime(2026, 11, 12, 7, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.STRIPE,
        'pi_ped_nov_03',
        True,
        [('Marraqueta', 150, Decimal('0.60')), ('Casero', 80, Decimal('0.70'))],
    ),
    (
        'Marcela Suárez Vaca',
        'jrivera',
        datetime(2026, 11, 13, 15, 30),
        datetime(2026, 11, 14, 16, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Gusanito', 25, Decimal('1.50')), ('Pan con Azúcar', 25, Decimal('1.00')), ('Pan Dulce', 20, Decimal('1.10'))],
    ),
    (
        'Colegio San Ignacio',
        'mgonzales',
        datetime(2026, 11, 16, 8, 45),
        datetime(2026, 11, 17, 8, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Pan Galleta', 120, Decimal('0.50')), ('Pan Mollete', 80, Decimal('0.60'))],
    ),
    (
        'Restaurante El Aljibe',
        'jrivera',
        datetime(2026, 11, 18, 14, 0),
        datetime(2026, 11, 19, 17, 30),
        EstadoPedido.ENTREGADO,
        MetodoPago.STRIPE,
        'pi_ped_nov_04',
        True,
        [('Arani', 60, Decimal('0.80')), ('Chama', 60, Decimal('0.90'))],
    ),
    (
        'Juan Pablo Áñez Rocha',
        'mgonzales',
        datetime(2026, 11, 20, 10, 0),
        datetime(2026, 11, 21, 9, 0),
        EstadoPedido.ENTREGADO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Tortilla', 30, Decimal('1.75')), ('Casero', 30, Decimal('0.70'))],
    ),
    (
        'Marcela Suárez Vaca',
        'jrivera',
        datetime(2026, 11, 21, 16, 45),
        datetime(2026, 11, 23, 17, 0),
        EstadoPedido.LISTO,
        MetodoPago.EFECTIVO,
        None,
        True,
        [('Pan Dulce', 30, Decimal('1.10')), ('Gusanito', 20, Decimal('1.50'))],
    ),
    (
        'Hotel Cortez',
        'mgonzales',
        datetime(2026, 11, 23, 8, 15),
        datetime(2026, 11, 24, 7, 0),
        EstadoPedido.EN_PREPARACION,
        MetodoPago.STRIPE,
        'pi_ped_nov_05',
        True,
        [('Marraqueta', 140, Decimal('0.60')), ('Casero', 60, Decimal('0.70')), ('Pan de Leche', 30, Decimal('1.25'))],
    ),
    (
        'Colegio San Ignacio',
        'jrivera',
        datetime(2026, 11, 23, 11, 30),
        datetime(2026, 11, 25, 8, 0),
        EstadoPedido.PENDIENTE,
        MetodoPago.STRIPE,
        None,
        False,
        [('Pan Mollete', 120, Decimal('0.60')), ('Pan Galleta', 100, Decimal('0.50'))],
    ),
]


class Command(BaseCommand):
    help = 'Puebla clientes y pedidos demo (CU14) con datos históricos y recientes de Noviembre.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Elimina pedidos demo y regenera la lista completa.',
        )

    def handle(self, *args, **options):
        usuarios = {u.nombre_usuario: u for u in Usuario.objects.all()}
        productos = {p.nombre: p for p in Producto.objects.all()}

        if not productos:
            self.stdout.write(
                self.style.ERROR('No hay productos en la base de datos. Ejecuta primero seed_productos.')
            )
            return

        usuario_default = Usuario.objects.filter(is_superuser=True).first() or Usuario.objects.first()

        tiene_noviembre = Pedido.objects.filter(
            fecha_registro__year=2026, fecha_registro__month=11
        ).exists()

        if tiene_noviembre and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {Pedido.objects.count()} pedidos registrados (incluye Noviembre). '
                    'Usa --force si deseas regenerarlos.'
                )
            )
            return

        with transaction.atomic():
            if options['force']:
                self.stdout.write('Limpiando pedidos previos...')
                Venta.objects.filter(id_pedido__isnull=False).update(id_pedido=None)
                MovimientoProductoTerminado.objects.filter(id_pedido__isnull=False).delete()
                DetallePedido.objects.all().delete()
                Pedido.objects.all().delete()

            # 1. Clientes
            clientes = {}
            for nombre, tel, dir_ in CLIENTES_DATA:
                cliente, _ = Cliente.objects.get_or_create(
                    nombre=nombre,
                    defaults={'telefono': tel, 'direccion': dir_},
                )
                clientes[nombre] = cliente

            # 2. Pedidos a registrar
            pedidos_a_cargar = []
            # Si no hay pedidos de septiembre, cargamos septiembre
            if not Pedido.objects.filter(fecha_registro__year=2026, fecha_registro__month=9).exists():
                pedidos_a_cargar.extend(PEDIDOS_SEPTIEMBRE)

            # Cargar siempre noviembre si no está
            if not Pedido.objects.filter(fecha_registro__year=2026, fecha_registro__month=11).exists():
                pedidos_a_cargar.extend(PEDIDOS_NOVIEMBRE)

            creados = 0
            for cli_nom, usr_nom, f_reg, f_ent, est, met, st_id, pag, items in pedidos_a_cargar:
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
                f'Poblado de Pedidos completado: {creados} pedidos registrados exitosamente.'
            )
        )
