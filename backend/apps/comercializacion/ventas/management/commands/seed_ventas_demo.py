"""
Comando de poblado de Ventas (CU13 y CU21).
Genera ventas históricas realistas con curva de demanda comercial por turnos:
- Septiembre y Octubre: base histórica inicial.
- Noviembre (1 al 23 de Noviembre, 2026): flujo operativo completo de 45 a 55 ventas
  por día hábil en dos turnos (08:00-12:00 con mgonzales, y 15:00-18:30 con jrivera).

Uso:
    python manage.py seed_ventas_demo [--force]
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import MovimientoProductoTerminado

MARCADOR_STRIPE = 'pi_demo_cu21_'

# Ventas históricas piloto para septiembre y octubre (base inicial previa)
VENTAS_BASE_PREVIAS = [
    ('2026-09-02', 9, 15, MetodoPago.EFECTIVO, 'mgonzales', [('Marraqueta', 30), ('Casero', 10)]),
    ('2026-09-04', 11, 20, MetodoPago.STRIPE, 'mgonzales', [('Pan Dulce', 8), ('Gusanito', 4)]),
    ('2026-09-07', 16, 40, MetodoPago.EFECTIVO, 'jrivera', [('Arani', 15), ('Tortilla', 4)]),
    ('2026-09-10', 8, 30, MetodoPago.EFECTIVO, 'mgonzales', [('Integral', 12), ('Chama', 10)]),
    ('2026-09-12', 10, 10, MetodoPago.STRIPE, 'mgonzales', [('Pan Mollete', 20), ('Pan Galleta', 16)]),
    ('2026-09-15', 15, 45, MetodoPago.EFECTIVO, 'jrivera', [('Marraqueta', 40), ('Pan con Azúcar', 8)]),
    ('2026-09-18', 12, 5, MetodoPago.EFECTIVO, 'mgonzales', [('Pan de Leche', 10), ('Casero', 8)]),
    ('2026-09-21', 17, 30, MetodoPago.STRIPE, 'jrivera', [('Tortilla', 6), ('Gusanito', 5)]),
    ('2026-09-24', 9, 50, MetodoPago.EFECTIVO, 'mgonzales', [('Arani', 20), ('Marraqueta', 25)]),
    ('2026-09-28', 13, 15, MetodoPago.EFECTIVO, 'mgonzales', [('Pan Dulce', 12), ('Integral', 8)]),
    ('2026-10-02', 9, 20, MetodoPago.EFECTIVO, 'mgonzales', [('Marraqueta', 35), ('Pan de Leche', 8)]),
    ('2026-10-05', 11, 35, MetodoPago.STRIPE, 'mgonzales', [('Arani', 18), ('Chama', 10)]),
    ('2026-10-08', 16, 15, MetodoPago.EFECTIVO, 'jrivera', [('Tortilla', 5), ('Casero', 12)]),
    ('2026-10-16', 8, 40, MetodoPago.STRIPE, 'mgonzales', [('Pan Dulce', 10), ('Gusanito', 6)]),
    ('2026-10-19', 10, 25, MetodoPago.EFECTIVO, 'mgonzales', [('Integral', 14), ('Pan con Azúcar', 10)]),
    ('2026-10-22', 15, 50, MetodoPago.EFECTIVO, 'jrivera', [('Marraqueta', 28), ('Pan Mollete', 15)]),
    ('2026-10-25', 12, 10, MetodoPago.STRIPE, 'mgonzales', [('Pan Galleta', 20), ('Pan de Leche', 8)]),
    ('2026-10-27', 17, 15, MetodoPago.EFECTIVO, 'jrivera', [('Arani', 16), ('Casero', 10)]),
    ('2026-10-31', 9, 45, MetodoPago.EFECTIVO, 'mgonzales', [('Marraqueta', 22), ('Tortilla', 3)]),
]

# Canastas representativas de compra en Santa Cruz
CANASTAS_MANANA_PICO = [
    [('Marraqueta', 10), ('Casero', 4)],
    [('Marraqueta', 15), ('Tortilla', 2)],
    [('Marraqueta', 8), ('Pan de Leche', 6)],
    [('Casero', 12), ('Integral', 6)],
    [('Marraqueta', 20)],
    [('Tortilla', 4), ('Casero', 8)],
    [('Pan de Leche', 8), ('Marraqueta', 10)],
    [('Integral', 10), ('Casero', 6)],
    [('Marraqueta', 6), ('Casero', 6), ('Pan de Leche', 4)],
    [('Casero', 15)],
]

CANASTAS_MANANA_VALLE = [
    [('Pan Mollete', 12), ('Pan Galleta', 10)],
    [('Integral', 6), ('Pan Galleta', 8)],
    [('Pan Mollete', 15)],
    [('Pan Galleta', 16), ('Integral', 4)],
    [('Casero', 8), ('Pan Mollete', 6)],
]

CANASTAS_TARDE_PICO = [
    [('Chama', 8), ('Arani', 6)],
    [('Pan Dulce', 6), ('Pan con Azúcar', 6)],
    [('Gusanito', 5), ('Chama', 6)],
    [('Arani', 10), ('Pan Dulce', 4)],
    [('Gusanito', 4), ('Pan con Azúcar', 6)],
    [('Chama', 10), ('Pan Dulce', 5)],
    [('Arani', 8), ('Pan con Azúcar', 5)],
    [('Pan de Leche', 6), ('Gusanito', 4)],
    [('Pan Dulce', 8), ('Arani', 6)],
    [('Chama', 6), ('Pan con Azúcar', 6), ('Gusanito', 2)],
]

CANASTAS_TARDE_CIERRE = [
    [('Marraqueta', 8), ('Chama', 4)],
    [('Arani', 6), ('Pan Dulce', 3)],
    [('Casero', 10), ('Pan Galleta', 6)],
    [('Pan con Azúcar', 6), ('Marraqueta', 6)],
]


class Command(BaseCommand):
    help = 'Puebla ventas históricas realistas (45-55 ventas/día en Noviembre) para demostración.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Elimina ventas demo previas y regenera el catálogo completo de noviembre.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Calcula las ventas y totales sin escribir en la base de datos.',
        )

    def handle(self, *args, **options):
        Usuario = get_user_model()
        cajera_manana = Usuario.objects.filter(nombre_usuario='mgonzales').first()
        cajera_tarde = Usuario.objects.filter(nombre_usuario='jrivera').first()

        if not cajera_manana or not cajera_tarde:
            raise CommandError(
                'Faltan las cajeras mgonzales y/o jrivera. Ejecuta primero python manage.py seed_usuarios.'
            )

        cajeras = {
            'mgonzales': cajera_manana,
            'jrivera': cajera_tarde,
        }

        productos = {p.nombre: p for p in Producto.objects.all()}
        if not productos:
            raise CommandError('No hay productos en la base de datos. Ejecuta seed_productos primero.')

        ventas_nov_existentes = Venta.objects.filter(
            fecha_hora__year=2026, fecha_hora__month=11
        ).count()

        # Si ya existen más de 200 ventas en noviembre y no pasaron --force, evitamos duplicación
        if ventas_nov_existentes >= 200 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {ventas_nov_existentes} ventas registradas en noviembre de 2026. '
                    'Usa --force si deseas regenerarlas.'
                )
            )
            return

        # Generar lista estructurada de ventas
        ventas_generadas = []
        rnd = random.Random(202611)  # Semilla fija para datos deterministas y reproducibles

        # 1. Base previa Septiembre y Octubre
        for fecha_str, h, m, metodo, usr_str, lineas in VENTAS_BASE_PREVIAS:
            f = date.fromisoformat(fecha_str)
            ventas_generadas.append({
                'fecha_hora': datetime(f.year, f.month, f.day, h, m),
                'metodo_pago': metodo,
                'cajera': cajeras[usr_str],
                'lineas': lineas,
                'es_stripe': (metodo == MetodoPago.STRIPE),
            })

        # 2. Generación diaria de Noviembre (del 1 al 23 de Noviembre de 2026)
        # Horario: 08:00 a 12:00 (mgonzales) y 15:00 a 18:30 (jrivera)
        fecha_actual = date(2026, 11, 1)
        fecha_fin = date(2026, 11, 23)

        while fecha_actual <= fecha_fin:
            dia_semana = fecha_actual.weekday()  # 0=Lunes, 5=Sábado, 6=Domingo

            if dia_semana == 6:
                # Domingo: turno matutino reducido (desayuno familiar, 16 ventas)
                minutos_disponibles = sorted(rnd.sample(range(8 * 60, 11 * 60 + 45), 16))
                for m_total in minutos_disponibles:
                    h, m = divmod(m_total, 60)
                    canasta = rnd.choice(CANASTAS_MANANA_PICO)
                    metodo = MetodoPago.STRIPE if rnd.random() < 0.20 else MetodoPago.EFECTIVO
                    ventas_generadas.append({
                        'fecha_hora': datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, h, m),
                        'metodo_pago': metodo,
                        'cajera': cajera_manana,
                        'lineas': canasta,
                        'es_stripe': (metodo == MetodoPago.STRIPE),
                    })
            else:
                # Lunes a Sábado: Día hábil completo (48 a 54 ventas por día)
                # Franja 1: Pico Desayuno 08:00 a 10:30 (~24 ventas)
                for m_total in sorted(rnd.sample(range(8 * 60, 10 * 60 + 30), rnd.randint(23, 26))):
                    h, m = divmod(m_total, 60)
                    canasta = rnd.choice(CANASTAS_MANANA_PICO)
                    metodo = MetodoPago.STRIPE if rnd.random() < 0.22 else MetodoPago.EFECTIVO
                    ventas_generadas.append({
                        'fecha_hora': datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, h, m),
                        'metodo_pago': metodo,
                        'cajera': cajera_manana,
                        'lineas': canasta,
                        'es_stripe': (metodo == MetodoPago.STRIPE),
                    })

                # Franja 2: Media mañana 10:30 a 12:00 (~6 ventas)
                for m_total in sorted(rnd.sample(range(10 * 60 + 30, 12 * 60), rnd.randint(5, 7))):
                    h, m = divmod(m_total, 60)
                    canasta = rnd.choice(CANASTAS_MANANA_VALLE)
                    metodo = MetodoPago.STRIPE if rnd.random() < 0.18 else MetodoPago.EFECTIVO
                    ventas_generadas.append({
                        'fecha_hora': datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, h, m),
                        'metodo_pago': metodo,
                        'cajera': cajera_manana,
                        'lineas': canasta,
                        'es_stripe': (metodo == MetodoPago.STRIPE),
                    })

                # [12:00 - 15:00: Almuerzo y preparación de hornos de la tarde - 0 ventas]

                # Franja 3: Pico Café/Té de la Tarde 15:00 a 17:30 (~16 ventas)
                for m_total in sorted(rnd.sample(range(15 * 60, 17 * 60 + 30), rnd.randint(15, 18))):
                    h, m = divmod(m_total, 60)
                    canasta = rnd.choice(CANASTAS_TARDE_PICO)
                    metodo = MetodoPago.STRIPE if rnd.random() < 0.28 else MetodoPago.EFECTIVO
                    ventas_generadas.append({
                        'fecha_hora': datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, h, m),
                        'metodo_pago': metodo,
                        'cajera': cajera_tarde,
                        'lineas': canasta,
                        'es_stripe': (metodo == MetodoPago.STRIPE),
                    })

                # Franja 4: Cierre de Mostrador 17:30 a 18:30 (~4 ventas)
                for m_total in sorted(rnd.sample(range(17 * 60 + 30, 18 * 60 + 30), rnd.randint(3, 5))):
                    h, m = divmod(m_total, 60)
                    canasta = rnd.choice(CANASTAS_TARDE_CIERRE)
                    metodo = MetodoPago.STRIPE if rnd.random() < 0.15 else MetodoPago.EFECTIVO
                    ventas_generadas.append({
                        'fecha_hora': datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, h, m),
                        'metodo_pago': metodo,
                        'cajera': cajera_tarde,
                        'lineas': canasta,
                        'es_stripe': (metodo == MetodoPago.STRIPE),
                    })

            fecha_actual += timedelta(days=1)

        # Orden cronológico estricto
        ventas_generadas.sort(key=lambda v: v['fecha_hora'])

        if options['dry_run']:
            total_estimado = Decimal('0.00')
            for v in ventas_generadas:
                for nom, cant in v['lineas']:
                    total_estimado += productos[nom].precio_venta * cant
            self.stdout.write(
                self.style.WARNING(
                    f'Simulación validada: {len(ventas_generadas)} ventas preparadas. '
                    f'Total proyectado: Bs {total_estimado:.2f}. No se guardó nada.'
                )
            )
            return

        with transaction.atomic():
            # Si forzaron o había muy pocas ventas en noviembre (el viejo demo de 11 ventas),
            # limpiamos las ventas de noviembre para evitar duplicaciones
            if options['force'] or ventas_nov_existentes < 200:
                self.stdout.write('Limpiando ventas previas de demostración para actualizar...')
                ventas_a_limpiar = Venta.objects.filter(
                    fecha_hora__year=2026, fecha_hora__month__in=[9, 10, 11]
                )
                ids_ventas = list(ventas_a_limpiar.values_list('id_venta', flat=True))
                # 1. Eliminar movimientos de producto terminado asociados
                MovimientoProductoTerminado.objects.filter(id_venta_id__in=ids_ventas).delete()
                # 2. Eliminar líneas de detalle protegidas (on_delete=models.PROTECT)
                DetalleVenta.objects.filter(id_venta_id__in=ids_ventas).delete()
                # 3. Eliminar cabeceras de venta
                ventas_a_limpiar.delete()

            siguiente_comprobante = _obtener_siguiente_comprobante()
            stripe_contador = 1
            total_facturado = Decimal('0.00')

            ventas_instancias = []
            detalles_por_venta = []

            for item in ventas_generadas:
                f_hora_aware = timezone.make_aware(item['fecha_hora'])
                total_venta = Decimal('0.00')
                lineas_db = []

                for prod_nom, cant in item['lineas']:
                    prod = productos[prod_nom]
                    p_unit = prod.precio_venta
                    subt = (p_unit * cant).quantize(Decimal('0.01'))
                    total_venta += subt
                    lineas_db.append((prod, cant, p_unit, subt))

                total_facturado += total_venta

                stripe_id = None
                if item['es_stripe']:
                    stripe_id = f'{MARCADOR_STRIPE}{stripe_contador:05d}'
                    stripe_contador += 1

                venta = Venta.objects.create(
                    id_usuario=item['cajera'],
                    numero_comprobante=siguiente_comprobante,
                    fecha_hora=f_hora_aware,
                    metodo_pago=item['metodo_pago'],
                    id_transaccion_stripe=stripe_id,
                    total=total_venta,
                )
                siguiente_comprobante += 1

                for prod, cant, p_unit, subt in lineas_db:
                    DetalleVenta.objects.create(
                        id_venta=venta,
                        id_producto=prod,
                        cantidad=cant,
                        precio_unitario=p_unit,
                        subtotal=subt,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'¡Ventas cargadas exitosamente!\n'
                f'  - Total transacciones: {len(ventas_generadas)}\n'
                f'  - Total facturado: Bs {total_facturado:,.2f}\n'
                f'  - Días cubiertos en Noviembre: 1 al 23 de Noviembre de 2026 (45-55 ventas/día hábil)'
            )
        )


def _obtener_siguiente_comprobante() -> int:
    ultima = Venta.objects.order_by('-numero_comprobante').first()
    if ultima is None:
        return 1
    return ultima.numero_comprobante + 1
