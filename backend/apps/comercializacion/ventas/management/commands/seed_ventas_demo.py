"""
Ventas de demostración para el CU21.

Cubre septiembre, octubre y noviembre de 2026, en efectivo y con tarjeta,
repartidas en varios días. No toca el stock ni las ventas que ya existían:
el reporte solo necesita filas en venta y detalle_venta.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.productos_inventario.productos.models import Producto

MARCADOR = 'pi_demo_cu21_'
CAJERA = 'mgonzales'

# fecha, hora, método, líneas (producto, unidades). El precio sale del catálogo.
VENTAS_DEMO = [
    ('2026-09-02', 9, MetodoPago.EFECTIVO, [('Marraqueta', 30), ('Casero', 10)]),
    ('2026-09-04', 11, MetodoPago.STRIPE, [('Pan Dulce', 8), ('Gusanito', 4)]),
    ('2026-09-07', 16, MetodoPago.EFECTIVO, [('Arani', 15), ('Tortilla', 4)]),
    ('2026-09-10', 8, MetodoPago.EFECTIVO, [('Integral', 12), ('Chama', 10)]),
    ('2026-09-12', 10, MetodoPago.STRIPE, [('Pan Mollete', 20), ('Pan Galleta', 16)]),
    ('2026-09-15', 15, MetodoPago.EFECTIVO, [('Marraqueta', 40), ('Pan con Azúcar', 8)]),
    ('2026-09-18', 12, MetodoPago.EFECTIVO, [('Pan de Leche', 10), ('Casero', 8)]),
    ('2026-09-21', 17, MetodoPago.STRIPE, [('Tortilla', 6), ('Gusanito', 5)]),
    ('2026-09-24', 9, MetodoPago.EFECTIVO, [('Arani', 20), ('Marraqueta', 25)]),
    ('2026-09-28', 13, MetodoPago.EFECTIVO, [('Pan Dulce', 12), ('Integral', 8)]),
    ('2026-10-02', 9, MetodoPago.EFECTIVO, [('Marraqueta', 35), ('Pan de Leche', 8)]),
    ('2026-10-05', 11, MetodoPago.STRIPE, [('Arani', 18), ('Chama', 10)]),
    ('2026-10-08', 16, MetodoPago.EFECTIVO, [('Tortilla', 5), ('Casero', 12)]),
    ('2026-10-16', 8, MetodoPago.STRIPE, [('Pan Dulce', 10), ('Gusanito', 6)]),
    ('2026-10-19', 10, MetodoPago.EFECTIVO, [('Integral', 14), ('Pan con Azúcar', 10)]),
    ('2026-10-22', 15, MetodoPago.EFECTIVO, [('Marraqueta', 28), ('Pan Mollete', 15)]),
    ('2026-10-25', 12, MetodoPago.STRIPE, [('Pan Galleta', 20), ('Pan de Leche', 8)]),
    ('2026-10-27', 17, MetodoPago.EFECTIVO, [('Arani', 16), ('Casero', 10)]),
    ('2026-10-31', 9, MetodoPago.EFECTIVO, [('Marraqueta', 22), ('Tortilla', 3)]),
    ('2026-11-01', 16, MetodoPago.STRIPE, [('Pan de Leche', 4), ('Gusanito', 2)]),
    ('2026-11-03', 9, MetodoPago.EFECTIVO, [('Marraqueta', 30), ('Casero', 8)]),
    ('2026-11-05', 11, MetodoPago.STRIPE, [('Pan Dulce', 9), ('Gusanito', 4)]),
    ('2026-11-07', 16, MetodoPago.EFECTIVO, [('Arani', 14), ('Pan de Leche', 7)]),
    ('2026-11-10', 8, MetodoPago.EFECTIVO, [('Integral', 10), ('Chama', 8)]),
    ('2026-11-12', 10, MetodoPago.STRIPE, [('Tortilla', 6), ('Pan Mollete', 12)]),
    ('2026-11-15', 15, MetodoPago.EFECTIVO, [('Marraqueta', 26), ('Pan con Azúcar', 9)]),
    ('2026-11-18', 12, MetodoPago.EFECTIVO, [('Pan Galleta', 18), ('Casero', 10)]),
    ('2026-11-21', 17, MetodoPago.STRIPE, [('Pan de Leche', 11), ('Gusanito', 5)]),
    ('2026-11-24', 9, MetodoPago.EFECTIVO, [('Arani', 20), ('Marraqueta', 18)]),
    ('2026-11-27', 13, MetodoPago.EFECTIVO, [('Pan Dulce', 8), ('Integral', 12)]),
]


class Command(BaseCommand):
    help = 'Carga ventas de septiembre a noviembre de 2026 para demostrar el CU21.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Revisa productos y cajera, sin guardar.',
        )

    def handle(self, *args, **options):
        if Venta.objects.filter(id_transaccion_stripe__startswith=MARCADOR).exists():
            self.stdout.write(self.style.WARNING('Las ventas de demostración del CU21 ya estaban cargadas.'))
            return

        Usuario = get_user_model()
        cajera = Usuario.objects.filter(nombre_usuario=CAJERA).first()
        if cajera is None:
            raise CommandError(f'No existe la cajera {CAJERA}.')

        nombres = {nombre for _, _, _, lineas in VENTAS_DEMO for nombre, _ in lineas}
        productos = {producto.nombre: producto for producto in Producto.objects.filter(nombre__in=nombres)}
        faltantes = sorted(nombres - productos.keys())
        if faltantes:
            raise CommandError(f'Faltan productos: {", ".join(faltantes)}.')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'Se crearían {len(VENTAS_DEMO)} ventas. No se guardó nada.'))
            return

        with transaction.atomic():
            siguiente = _siguiente_comprobante()
            tarjeta = 1
            for fecha, hora, metodo, lineas in VENTAS_DEMO:
                anio, mes, dia = (int(parte) for parte in fecha.split('-'))
                cuando = timezone.make_aware(datetime(anio, mes, dia, hora, 15))
                detalles = []
                total = Decimal('0.00')
                for nombre, cantidad in lineas:
                    precio = productos[nombre].precio_venta
                    subtotal = (precio * cantidad).quantize(Decimal('0.01'))
                    total += subtotal
                    detalles.append((productos[nombre], cantidad, precio, subtotal))
                stripe = None
                if metodo == MetodoPago.STRIPE:
                    stripe = f'{MARCADOR}{tarjeta:03d}'
                    tarjeta += 1
                venta = Venta.objects.create(
                    id_usuario=cajera,
                    numero_comprobante=siguiente,
                    fecha_hora=cuando,
                    metodo_pago=metodo,
                    id_transaccion_stripe=stripe,
                    total=total,
                )
                DetalleVenta.objects.bulk_create([
                    DetalleVenta(
                        id_venta=venta,
                        id_producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                    )
                    for producto, cantidad, precio, subtotal in detalles
                ])
                siguiente += 1

        self.stdout.write(self.style.SUCCESS(f'Se cargaron {len(VENTAS_DEMO)} ventas de demostración.'))


def _siguiente_comprobante() -> int:
    ultima = Venta.objects.order_by('-numero_comprobante').first()
    if ultima is None:
        return 1
    return ultima.numero_comprobante + 1
