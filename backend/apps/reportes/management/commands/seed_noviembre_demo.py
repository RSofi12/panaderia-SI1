"""
Comando de Poblado de Operaciones para Noviembre 2026 (CU25, CU21, CU24, CU23).
Panadería Santiago (SI-1).

Puebla el período del 1 al 22 de Noviembre de 2026:
- 22 días de ventas continuas en mostrador (400+ ventas, efectivo y tarjeta).
- Compras semanales de materias primas a proveedores.
- Bajas y mermas de productos terminados en vitrina.
- Gastos operativos (alquiler, luz, agua, mantenimiento) e inversiones (bandejas, balanza).

Permite probar CU25 (Resultados Económicos) tanto en vista diaria (hoy 22/11/2026),
como en vista semanal (semana actual 47) y vista mensual (Noviembre 2026 completo).

Uso:
    python manage.py seed_noviembre_demo
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.compras.gastos.models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)
from apps.compras.proveedores.models import Proveedor
from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.produccion.models import DetalleProduccion, JornadaProduccion, Produccion
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
    TipoMovimientoProductoTerminado,
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla operaciones realistas de Noviembre 2026 (días 1 al 22) para pruebas de CU25 y balances.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la ejecución aunque ya existan datos de noviembre.',
        )
        parser.add_argument(
            '--solo-produccion',
            action='store_true',
            help='Solo crea jornadas de horno (CU22). No duplica ventas, compras ni gastos.',
        )

    def handle(self, *args, **options):
        solo_produccion = options.get('solo_produccion', False)
        self.stdout.write(self.style.NOTICE(
            '============================================================\n'
            '  POBLANDO NOVIEMBRE 2026 (01/11/2026 - 22/11/2026)        \n'
            '============================================================'
        ))

        # 1. Validaciones
        cajeras = list(Usuario.objects.filter(nombre_usuario__in=['mgonzales', 'jrivera']))
        if not cajeras:
            cajeras = list(Usuario.objects.all()[:2])
        propietario = (
            Usuario.objects.filter(nombre_usuario='csantiago').first()
            or Usuario.objects.filter(is_superuser=True).first()
        )
        panadero = (
            Usuario.objects.filter(nombre_usuario__in=['mrojas', 'ptorrez']).first()
            or propietario
        )

        productos = list(Producto.objects.filter(activo=True))
        if not productos:
            self.stdout.write(self.style.ERROR('No hay productos registrados. Ejecute seed_productos primero.'))
            return

        materias = list(MateriaPrima.objects.filter(activo=True))
        proveedores = list(Proveedor.objects.filter(activo=True))

        rng = random.Random(202611)

        # 2. Número de comprobante base
        max_comp = Venta.objects.aggregate(m=Max('numero_comprobante'))['m'] or 25000
        comp_cursor = max_comp + 1

        tz = timezone.get_current_timezone()
        with transaction.atomic():
            # =================================================================
            # A. GASTOS E INVERSIONES DE NOVIEMBRE 2026 (CU20 / CU25)
            # =================================================================
            gastos_data = [
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.ALQUILER,
                    'Alquiler de local comercial (Noviembre 2026)',
                    'Canon de arrendamiento mensual del local de Panadería Santiago',
                    Decimal('2800.00'),
                    timezone.make_aware(datetime(2026, 11, 2, 9, 30), tz),
                ),
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.SERVICIOS,
                    'Energía eléctrica CRE (Amasadoras y Hornos)',
                    'Factura de electricidad correspondiente al consumo de producción',
                    Decimal('1280.50'),
                    timezone.make_aware(datetime(2026, 11, 5, 10, 15), tz),
                ),
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.SERVICIOS,
                    'Agua potable Saguapac',
                    'Consumo de agua potable y saneamiento del establecimiento',
                    Decimal('345.00'),
                    timezone.make_aware(datetime(2026, 11, 6, 11, 0), tz),
                ),
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.OTROS,
                    'Bolsas kraft y cajas para panadería',
                    'Adquisición de 2000 bolsas de papel kraft impresas con logotipo',
                    Decimal('450.00'),
                    timezone.make_aware(datetime(2026, 11, 10, 14, 0), tz),
                ),
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.MANTENIMIENTO,
                    'Mantenimiento preventivo amasadora industrial',
                    'Cambio de correas y lubricación de rodamientos de amasadora de 25kg',
                    Decimal('380.00'),
                    timezone.make_aware(datetime(2026, 11, 12, 16, 20), tz),
                ),
                (
                    TipoMovimientoEconomico.INVERSION,
                    CategoriaMovimientoEconomico.EQUIPOS,
                    '10 Bandejas acanaladas bagueteras de aluminio',
                    'Nuevas bandejas antiadherentes perforadas para horneado de baguettes',
                    Decimal('980.00'),
                    timezone.make_aware(datetime(2026, 11, 15, 11, 30), tz),
                ),
                (
                    TipoMovimientoEconomico.INVERSION,
                    CategoriaMovimientoEconomico.EQUIPOS,
                    'Balanza digital gramera de precisión',
                    'Balanza digital de acero inoxidable para control estricto de recetas BOM',
                    Decimal('420.00'),
                    timezone.make_aware(datetime(2026, 11, 18, 15, 0), tz),
                ),
                (
                    TipoMovimientoEconomico.GASTO,
                    CategoriaMovimientoEconomico.SERVICIOS,
                    'Gas licuado GLP / YPFB',
                    'Reposición de cilindros industriales de gas para hornos',
                    Decimal('560.00'),
                    timezone.make_aware(datetime(2026, 11, 19, 8, 45), tz),
                ),
            ]

            total_gastos_creados = 0
            if solo_produccion:
                gastos_data = []
            for tipo, cat, conc, desc, monto, fecha_h in gastos_data:
                g, created = MovimientoEconomico.objects.get_or_create(
                    concepto=conc,
                    fecha_hora=fecha_h,
                    defaults={
                        'tipo': tipo,
                        'categoria': cat,
                        'descripcion': desc,
                        'monto': monto,
                        'id_usuario': propietario,
                        'anulado': False,
                    },
                )
                if created:
                    total_gastos_creados += 1

            if not solo_produccion:
                self.stdout.write(f'  [OK] {total_gastos_creados} Gastos e Inversiones creados para Noviembre.')

            # =================================================================
            # B. COMPRAS DE MATERIA PRIMA (CU07 / CU25)
            # =================================================================
            dias_compras = [] if solo_produccion else [2, 6, 9, 13, 16, 20]
            total_compras_creadas = 0

            PRECIOS_MP = {
                'Harina': Decimal('4.50'),
                'Azúcar': Decimal('6.00'),
                'Sal': Decimal('3.00'),
                'Levadura': Decimal('45.00'),
                'Manteca': Decimal('18.00'),
                'Mantequilla': Decimal('35.00'),
                'Leche': Decimal('7.50'),
                'Huevos': Decimal('0.90'),
                'Queso': Decimal('28.00'),
                'Queso Chaqueño': Decimal('30.00'),
                'Almidón de Yuca': Decimal('14.00'),
            }

            for dia_c in dias_compras:
                fecha_compra = timezone.make_aware(datetime(2026, 11, dia_c, 8, rng.randint(0, 50)), tz)
                proveedor = rng.choice(proveedores) if proveedores else None
                if not proveedor:
                    continue

                compra = Compra.objects.create(
                    id_usuario=propietario,
                    id_proveedor=proveedor,
                    fecha_hora=fecha_compra,
                    total=Decimal('0.00'),
                )

                subtotal_compra = Decimal('0.00')
                items_mp = rng.sample(materias, k=min(len(materias), rng.randint(2, 4)))
                for mp in items_mp:
                    cant = Decimal(str(rng.randint(20, 100)))
                    precio_u = PRECIOS_MP.get(mp.nombre, Decimal('10.00'))
                    subt = (cant * precio_u).quantize(Decimal('0.01'))
                    DetalleCompra.objects.create(
                        id_compra=compra,
                        id_materia_prima=mp,
                        cantidad=cant,
                        precio_unitario=precio_u,
                        subtotal=subt,
                    )
                    subtotal_compra += subt

                compra.total = subtotal_compra
                compra.save()
                total_compras_creadas += 1

            if not solo_produccion:
                self.stdout.write(f'  [OK] {total_compras_creadas} Compras de Materia Prima creadas en Noviembre.')

            # =================================================================
            # C. PRODUCCIÓN Y MERMAS DIARIAS (CU10 / CU18 / CU25)
            # =================================================================
            total_mermas_creadas = 0
            total_lotes_creados = 0
            for dia_n in range(1, 23):
                fecha_p = date(2026, 11, dia_n)
                if Produccion.objects.filter(fecha=fecha_p, jornada=JornadaProduccion.MANANA).exists():
                    continue
                # Crear lote de producción diario
                prod = Produccion.objects.create(
                    id_usuario=panadero,
                    fecha=fecha_p,
                    jornada=JornadaProduccion.MANANA,
                )

                # Detalles de producción para 3 productos
                prod_selec = rng.sample(productos, k=min(len(productos), 3))
                detalles_creados = []
                for p in prod_selec:
                    cant_p = rng.randint(50, 120)
                    costo_u = (p.precio_venta * Decimal('0.40')).quantize(Decimal('0.01'))
                    det = DetalleProduccion.objects.create(
                        id_produccion=prod,
                        id_producto=p,
                        cantidad_producida=cant_p,
                        costo_unitario=costo_u,
                    )
                    detalles_creados.append(det)

                # Cada 2 o 3 días, registrar una merma de mostrador (CU18)
                if dia_n % 2 == 0 and detalles_creados:
                    det_merma = detalles_creados[0]
                    cant_merma = rng.randint(4, 12)
                    hora_merma = timezone.make_aware(datetime(2026, 11, dia_n, 14, 30), tz)
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=det_merma,
                        id_usuario=panadero,
                        cantidad=cant_merma,
                        costo_unitario=det_merma.costo_unitario,
                        fecha_salida=hora_merma,
                    )
                    total_mermas_creadas += 1
                total_lotes_creados += 1

            self.stdout.write(
                f'  [OK] {total_lotes_creados} Jornadas de producción y '
                f'{total_mermas_creadas} Notas de Merma registradas.'
            )

            # =================================================================
            # D. VENTAS DIARIAS EN MOSTRADOR (01/11/2026 al 22/11/2026)
            # =================================================================
            total_ventas = 0
            total_recaudado = Decimal('0.00')

            if solo_produccion:
                self.stdout.write('  [SKIP] Ventas omitidas (--solo-produccion).')
            else:
                for dia_n in range(1, 23):
                    fecha_v = date(2026, 11, dia_n)
                    num_ventas = rng.randint(18, 26)  # 18 a 26 ventas por día

                    for _ in range(num_ventas):
                        cajera = rng.choice(cajeras)
                        # Hora entre 06:30 y 14:00
                        h = rng.randint(6, 13)
                        m = rng.randint(0, 59)
                        hora_venta = timezone.make_aware(datetime.combine(fecha_v, time(h, m)), tz)

                        metodo = MetodoPago.STRIPE if rng.random() < 0.25 else MetodoPago.EFECTIVO
                        stripe_id = f'pi_mes_nov_{dia_n}_{comp_cursor}' if metodo == MetodoPago.STRIPE else None

                        venta = Venta.objects.create(
                            id_usuario=cajera,
                            numero_comprobante=comp_cursor,
                            fecha_hora=hora_venta,
                            metodo_pago=metodo,
                            id_transaccion_stripe=stripe_id,
                            total=Decimal('0.00'),
                        )
                        comp_cursor += 1

                        subtotal_venta = Decimal('0.00')
                        # Cada ticket lleva de 1 a 3 productos distintos
                        k_prods = rng.randint(1, 3)
                        prods_ticket = rng.sample(productos, k=min(len(productos), k_prods))

                        for p in prods_ticket:
                            cant = rng.randint(2, 15)  # 2 a 15 panes
                            precio_u = p.precio_venta or Decimal('1.00')
                            subt = (Decimal(cant) * precio_u).quantize(Decimal('0.01'))

                            DetalleVenta.objects.create(
                                id_venta=venta,
                                id_producto=p,
                                cantidad=cant,
                                precio_unitario=precio_u,
                                subtotal=subt,
                            )
                            subtotal_venta += subt

                        venta.total = subtotal_venta
                        venta.save()
                        total_ventas += 1
                        total_recaudado += subtotal_venta

            self.stdout.write(self.style.SUCCESS(
                f'\n============================================================\n'
                f'POBLADO DE NOVIEMBRE 2026 COMPLETADO CON ÉXITO:\n'
                f' - Ventas registradas: {total_ventas} tickets\n'
                f' - Total facturado en Noviembre: Bs {total_recaudado:,.2f}\n'
                f' - Compras de materia prima: {total_compras_creadas} compras\n'
                f' - Gastos e inversiones: {total_gastos_creados} registros\n'
                f' - Notas de merma: {total_mermas_creadas} pérdidas registradas\n'
                f'============================================================'
            ))
