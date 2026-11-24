"""
Comando de Poblado para Meses Operativos Completos (Septiembre y Octubre 2026) — Panadería Santiago (SI-1).

Simula la operación comercial y productiva de Septiembre y Octubre de 2026:
- Septiembre 2026: 26 jornadas laborales (L-S), 35 a 40 ventas/día, compras semanales,
  producción continua, pedidos institucionales e inversión del horno industrial (Bs 8.000).
- Octubre 2026: 27 jornadas laborales (L-S), 35 a 40 ventas/día, compras semanales,
  producción continua, pedidos institucionales y gastos operativos regulares.

Uso:
    python manage.py seed_mes_operativo [--force] [--mes 9|10]
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.comercializacion.pedidos.models import (
    Cliente,
    DetallePedido,
    EstadoPedido,
    Pedido,
)
from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.compras.gastos.models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)
from apps.compras.proveedores.models import Proveedor
from apps.productos_inventario.materia_prima.models import (
    InventarioMateriaPrima,
    MateriaPrima,
)
from apps.productos_inventario.produccion.models import (
    DetalleProduccion,
    JornadaProduccion,
    Produccion,
)
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    NotaPerdidaProducto,
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla meses operativos completos (Septiembre y Octubre 2026, 35-40 ventas/día hábil) con ganancias coherentes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecuta la población incluso si ya existen registros de septiembre u octubre.',
        )
        parser.add_argument(
            '--mes',
            type=int,
            choices=[9, 10],
            help='Especifica si se quiere poblar únicamente Septiembre (9) u Octubre (10). Por defecto ambos.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIME(
            '============================================================\n'
            '  POBLADO DE MESES OPERATIVOS (SEPTIEMBRE Y OCTUBRE 2026)   \n'
            '============================================================'
        ) if hasattr(self.style, 'MIME') else self.style.NOTICE(
            '============================================================\n'
            '  POBLADO DE MESES OPERATIVOS (SEPTIEMBRE Y OCTUBRE 2026)   \n'
            '============================================================'
        ))

        # 1. Prerrequisitos
        usuarios = {u.nombre_usuario: u for u in Usuario.objects.all()}
        if not usuarios:
            self.stdout.write(self.style.ERROR('No hay usuarios registrados. Ejecute primero seed_usuarios.'))
            return

        cajeras = [u for u in [usuarios.get('mgonzales'), usuarios.get('jrivera')] if u]
        if not cajeras:
            cajeras = [list(usuarios.values())[0]]

        panaderos = [u for u in [usuarios.get('mrojas'), usuarios.get('ptorrez')] if u]
        if not panaderos:
            panaderos = [list(usuarios.values())[0]]

        admin_user = usuarios.get('admin') or usuarios.get('csantiago') or list(usuarios.values())[0]

        productos = list(Producto.objects.filter(activo=True))
        if not productos:
            self.stdout.write(self.style.ERROR('No hay productos registrados. Ejecute primero seed_productos.'))
            return

        proveedores = list(Proveedor.objects.filter(activo=True))
        if not proveedores:
            self.stdout.write(self.style.ERROR('No hay proveedores registrados. Ejecute primero seed_proveedores.'))
            return

        materias = list(MateriaPrima.objects.filter(activo=True))
        if not materias:
            self.stdout.write(self.style.ERROR('No hay materias primas registradas. Ejecute primero seed_materias_primas.'))
            return

        clientes = list(Cliente.objects.all())
        if not clientes:
            clientes_data = [
                ('Rosa Fernández Choque', '70011122', 'Av. Banzer, 3er anillo'),
                ('Hotel Cortez', '33421100', 'Av. Cristo Redentor, 3er anillo'),
                ('Juan Pablo Áñez Rocha', '70055443', 'Calle Beni, casi 2do anillo'),
                ('Colegio San Ignacio', '33450099', 'Av. Alemana, 4to anillo'),
                ('Marcela Suárez Vaca', '70099887', 'Barrio Urbari, 2do anillo'),
                ('Restaurante El Aljibe', '33500221', 'Av. San Martín, 2do anillo'),
            ]
            for nom, tel, dir_c in clientes_data:
                c, _ = Cliente.objects.get_or_create(
                    nombre=nom,
                    defaults={'telefono': tel, 'direccion': dir_c},
                )
                clientes.append(c)

        meses_a_procesar = [options['mes']] if options.get('mes') else [9, 10]

        for num_mes in meses_a_procesar:
            self._poblar_mes(
                mes=num_mes,
                force=options.get('force', False),
                usuarios=usuarios,
                cajeras=cajeras,
                panaderos=panaderos,
                admin_user=admin_user,
                productos=productos,
                proveedores=proveedores,
                materias=materias,
                clientes=clientes,
            )

    def _poblar_mes(self, *, mes, force, usuarios, cajeras, panaderos, admin_user, productos, proveedores, materias, clientes):
        nombre_mes = 'Septiembre' if mes == 9 else 'Octubre'
        prefijo_stripe = 'pi_mes_sep_' if mes == 9 else 'pi_mes_oct_'
        seed_rnd = 202609 if mes == 9 else 202610
        rng = random.Random(seed_rnd)

        self.stdout.write(self.style.NOTICE(f'\n--- Procesando {nombre_mes} 2026 ---'))

        # Verificar si ya tiene datos
        ventas_mes = Venta.objects.filter(
            fecha_hora__year=2026, fecha_hora__month=mes
        ).count()

        if ventas_mes >= 500 and not force:
            self.stdout.write(self.style.WARNING(
                f'{nombre_mes} 2026 ya cuenta con {ventas_mes} ventas. Use --force para regenerar.'
            ))
            return

        # Siguiente número de comprobante único
        max_comp = Venta.objects.aggregate(m=Max('numero_comprobante'))['m'] or 1000
        numero_comprobante = max_comp + 1

        # Rango de fechas
        ultimo_dia = 30 if mes == 9 else 31
        dias_operativos = []
        fecha_cursor = date(2026, mes, 1)
        fecha_fin = date(2026, mes, ultimo_dia)

        while fecha_cursor <= fecha_fin:
            # 0=Lunes ... 5=Sábado, 6=Domingo
            if fecha_cursor.weekday() < 6:
                dias_operativos.append(fecha_cursor)
            fecha_cursor += timedelta(days=1)

        self.stdout.write(f'Jornadas laborales a simular en {nombre_mes}: {len(dias_operativos)} días (Lunes a Sábado)')

        with transaction.atomic():
            if force or ventas_mes < 500:
                # Limpiar ventas previas de ese mes si se solicita regeneración
                Venta.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes).delete()
                # Limpiar compras del mes si existían de simulaciones previas
                Compra.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes).delete()
                # Limpiar producciones del mes
                Produccion.objects.filter(fecha__year=2026, fecha__month=mes).delete()
                # Limpiar gastos del mes
                MovimientoEconomico.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes).delete()
                # Limpiar pedidos del mes
                Pedido.objects.filter(fecha_registro__year=2026, fecha_registro__month=mes).delete()

            # A. COMPRAS SEMANALES RECURRENTES DE MATERIA PRIMA
            # 14 a 16 compras repartidas en el mes
            total_compras_creadas = 0
            total_gastado_mp = Decimal('0.00')

            dias_compras = [1, 3, 5, 8, 10, 12, 15, 17, 19, 22, 24, 26, 28] if mes == 9 else [2, 5, 7, 9, 12, 14, 16, 19, 21, 23, 26, 28, 30]
            for d in dias_compras:
                if d <= ultimo_dia:
                    f_compra = date(2026, mes, d)
                    prov = proveedores[d % len(proveedores)]
                    dt_compra = timezone.make_aware(datetime.combine(f_compra, time(8, 0)))

                    compra = Compra.objects.create(
                        id_proveedor=prov,
                        id_usuario=admin_user,
                        fecha_hora=dt_compra,
                        total=Decimal('0.00'),
                    )
                    total_compras_creadas += 1

                    items_mp = rng.sample(materias, k=min(4, len(materias)))
                    total_c = Decimal('0.00')
                    for mp in items_mp:
                        cant = Decimal(str(rng.randint(30, 80)))
                        p_unit = Decimal(str(rng.choice([4.50, 6.00, 7.50, 3.00, 0.90, 35.00])))
                        subt = (cant * p_unit).quantize(Decimal('0.01'))
                        DetalleCompra.objects.create(
                            id_compra=compra,
                            id_materia_prima=mp,
                            cantidad=cant,
                            precio_unitario=p_unit,
                            subtotal=subt,
                        )
                        total_c += subt

                    compra.total = total_c
                    compra.save(update_fields=['total'])
                    total_gastado_mp += total_c

            # B. JORNADAS DE PRODUCCIÓN, VENTAS Y PEDIDOS POR CADA DÍA HÁBIL
            total_ventas_creadas = 0
            total_ingresos_ventas = Decimal('0.00')
            total_producciones_creadas = 0
            total_pedidos_creados = 0
            total_ingresos_pedidos = Decimal('0.00')

            stripe_contador = 1
            ped_stripe_contador = 1

            for dia in dias_operativos:
                es_sabado = (dia.weekday() == 5)
                panadero = rng.choice(panaderos)
                cajera_m = usuarios.get('mgonzales') or cajeras[0]
                cajera_t = usuarios.get('jrivera') or cajeras[-1]

                # 1. Producción diaria de pan horneado fresco (05:15 am)
                prod = Produccion.objects.create(
                    id_usuario=panadero,
                    fecha=dia,
                    jornada=JornadaProduccion.MANANA,
                )
                total_producciones_creadas += 1

                detalles_prod_creados = []
                for p in productos:
                    cant_p = rng.randint(60, 180) if 'Marraqueta' in p.nombre or 'Casero' in p.nombre else rng.randint(25, 60)
                    dp = DetalleProduccion.objects.create(
                        id_produccion=prod,
                        id_producto=p,
                        cantidad_producida=cant_p,
                        costo_unitario=p.costo_produccion,
                    )
                    detalles_prod_creados.append(dp)

                # Merma ocasional (cada 3 días, 3 a 5 panes)
                if dia.day % 3 == 0 and detalles_prod_creados:
                    dp_merma = rng.choice(detalles_prod_creados)
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=dp_merma,
                        id_usuario=panadero,
                        cantidad=rng.randint(2, 5),
                        costo_unitario=dp_merma.costo_unitario,
                        fecha_salida=timezone.make_aware(datetime.combine(dia, time(14, 0))),
                    )

                # 2. Ventas diarias de mostrador: 35 a 40 ventas por día hábil
                num_ventas = rng.randint(35, 40)
                # Repartidas en dos turnos: Mañana (08:00 - 12:00) y Tarde (15:00 - 18:30)
                n_manana = int(num_ventas * 0.60)
                n_tarde = num_ventas - n_manana

                minutos_manana = sorted(rng.sample(range(8 * 60, 12 * 60), n_manana))
                minutos_tarde = sorted(rng.sample(range(15 * 60, 18 * 60 + 30), n_tarde))

                for m_total in minutos_manana:
                    h, m = divmod(m_total, 60)
                    dt_venta = timezone.make_aware(datetime.combine(dia, time(h, m)))
                    es_stripe = (rng.random() < 0.25)
                    metodo = MetodoPago.STRIPE if es_stripe else MetodoPago.EFECTIVO
                    stripe_id = f'{prefijo_stripe}{stripe_contador:05d}' if es_stripe else None
                    if es_stripe:
                        stripe_contador += 1

                    v = Venta.objects.create(
                        id_usuario=cajera_m,
                        numero_comprobante=numero_comprobante,
                        fecha_hora=dt_venta,
                        metodo_pago=metodo,
                        id_transaccion_stripe=stripe_id,
                        total=Decimal('0.00'),
                    )
                    numero_comprobante += 1
                    total_ventas_creadas += 1

                    # Líneas de venta (ticket promedio ~Bs 12-14)
                    prods_ticket = rng.sample(productos, k=rng.randint(1, 3))
                    total_v = Decimal('0.00')
                    for p_sel in prods_ticket:
                        cant_v = rng.randint(4, 15) if 'Marraqueta' in p_sel.nombre or 'Casero' in p_sel.nombre else rng.randint(2, 8)
                        subt = (p_sel.precio_venta * cant_v).quantize(Decimal('0.01'))
                        DetalleVenta.objects.create(
                            id_venta=v,
                            id_producto=p_sel,
                            cantidad=cant_v,
                            precio_unitario=p_sel.precio_venta,
                            subtotal=subt,
                        )
                        total_v += subt
                    v.total = total_v
                    v.save(update_fields=['total'])
                    total_ingresos_ventas += total_v

                for m_total in minutos_tarde:
                    h, m = divmod(m_total, 60)
                    dt_venta = timezone.make_aware(datetime.combine(dia, time(h, m)))
                    es_stripe = (rng.random() < 0.25)
                    metodo = MetodoPago.STRIPE if es_stripe else MetodoPago.EFECTIVO
                    stripe_id = f'{prefijo_stripe}{stripe_contador:05d}' if es_stripe else None
                    if es_stripe:
                        stripe_contador += 1

                    v = Venta.objects.create(
                        id_usuario=cajera_t,
                        numero_comprobante=numero_comprobante,
                        fecha_hora=dt_venta,
                        metodo_pago=metodo,
                        id_transaccion_stripe=stripe_id,
                        total=Decimal('0.00'),
                    )
                    numero_comprobante += 1
                    total_ventas_creadas += 1

                    prods_ticket = rng.sample(productos, k=rng.randint(1, 3))
                    total_v = Decimal('0.00')
                    for p_sel in prods_ticket:
                        cant_v = rng.randint(2, 6)
                        subt = (p_sel.precio_venta * cant_v).quantize(Decimal('0.01'))
                        DetalleVenta.objects.create(
                            id_venta=v,
                            id_producto=p_sel,
                            cantidad=cant_v,
                            precio_unitario=p_sel.precio_venta,
                            subtotal=subt,
                        )
                        total_v += subt
                    v.total = total_v
                    v.save(update_fields=['total'])
                    total_ingresos_ventas += total_v

                # 3. Pedidos anticipados (1 pedido cada 1-2 días hábiles)
                if rng.random() < 0.75:
                    cliente_sel = rng.choice(clientes)
                    dt_reg = timezone.make_aware(datetime.combine(dia, time(7, 30)))
                    dt_ent = timezone.make_aware(datetime.combine(dia, time(rng.randint(9, 17), 0)))
                    ped_stripe = (rng.random() < 0.35)
                    metodo_ped = MetodoPago.STRIPE if ped_stripe else MetodoPago.EFECTIVO
                    stripe_ped_id = f'{prefijo_stripe}ped_{ped_stripe_contador:04d}' if ped_stripe else None
                    if ped_stripe:
                        ped_stripe_contador += 1

                    pedido = Pedido.objects.create(
                        id_cliente=cliente_sel,
                        id_usuario=cajera_m,
                        fecha_registro=dt_reg,
                        fecha_entrega=dt_ent,
                        estado=EstadoPedido.ENTREGADO,
                        metodo_pago=metodo_ped,
                        id_transaccion_stripe=stripe_ped_id,
                        pagado=True,
                        total=Decimal('0.00'),
                    )
                    total_pedidos_creados += 1

                    prods_ped = rng.sample(productos, k=rng.randint(2, 3))
                    total_p = Decimal('0.00')
                    for p_sel in prods_ped:
                        cant_ped = rng.randint(15, 45)
                        subt_ped = (p_sel.precio_venta * cant_ped).quantize(Decimal('0.01'))
                        DetallePedido.objects.create(
                            id_pedido=pedido,
                            id_producto=p_sel,
                            cantidad=cant_ped,
                            precio_unitario=p_sel.precio_venta,
                            subtotal=subt_ped,
                        )
                        total_p += subt_ped

                    pedido.total = total_p
                    pedido.save(update_fields=['total'])
                    total_ingresos_pedidos += total_p

            # C. GASTOS E INVERSIONES DEL MES (CU20)
            total_gastos_op = Decimal('0.00')
            total_inversiones = Decimal('0.00')

            if mes == 9:
                movimientos_mes = [
                    (date(2026, 9, 2), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.ALQUILER, 'Alquiler del local comercial', 'Pago mensual de alquiler del establecimiento', Decimal('1500.00')),
                    (date(2026, 9, 6), TipoMovimientoEconomico.INVERSION, CategoriaMovimientoEconomico.EQUIPOS, 'Compra de horno industrial rotativo', 'Nuevo horno industrial para incrementar capacidad de producción', Decimal('8000.00')),
                    (date(2026, 9, 8), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Energía eléctrica CRE', 'Factura de energía eléctrica trifásica', Decimal('350.00')),
                    (date(2026, 9, 9), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Agua potable SAGUAPAC', 'Consumo mensual de agua potable', Decimal('120.00')),
                    (date(2026, 9, 18), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.MANTENIMIENTO, 'Mantenimiento preventivo de hornos', 'Servicio técnico preventivo de hornos y amasadora', Decimal('200.00')),
                ]
            else:
                movimientos_mes = [
                    (date(2026, 10, 2), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.ALQUILER, 'Alquiler mensual del local comercial', 'Pago mensual al arrendador del inmueble comercial', Decimal('2800.00')),
                    (date(2026, 10, 8), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Energía Eléctrica CRE', 'Factura de luz trifásica para hornos y cámaras', Decimal('1450.00')),
                    (date(2026, 10, 10), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Agua potable SAGUAPAC', 'Consumo mensual de agua potable para producción', Decimal('320.00')),
                    (date(2026, 10, 15), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.MANTENIMIENTO, 'Mantenimiento preventivo de hornos y amasadora', 'Lubricación de rodamientos y revisión de quemadores', Decimal('650.00')),
                    (date(2026, 10, 22), TipoMovimientoEconomico.INVERSION, CategoriaMovimientoEconomico.EQUIPOS, 'Bandejas de acero y canastas de mostrador', 'Inversión en 15 bandejas perforadas y canastas artesanales', Decimal('580.00')),
                    (date(2026, 10, 29), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.OTROS, 'Artículos de desinfección y limpieza industrial', 'Detergentes grado alimenticio y toallas para higiene', Decimal('220.00')),
                ]

            for f_gasto, tipo_g, cat_g, conc_g, desc_g, monto_g in movimientos_mes:
                MovimientoEconomico.objects.create(
                    id_usuario=admin_user,
                    tipo=tipo_g,
                    categoria=cat_g,
                    concepto=conc_g,
                    descripcion=desc_g,
                    monto=monto_g,
                    fecha_hora=timezone.make_aware(datetime.combine(f_gasto, time(10, 0))),
                )
                if tipo_g == TipoMovimientoEconomico.GASTO:
                    total_gastos_op += monto_g
                else:
                    total_inversiones += monto_g

            # D. AJUSTE DE EXISTENCIAS FINALES
            for p in productos:
                InventarioProductoTerminado.objects.update_or_create(
                    id_producto=p,
                    defaults={'stock_actual': rng.randint(40, 140)},
                )

            for m in materias:
                InventarioMateriaPrima.objects.update_or_create(
                    id_materia_prima=m,
                    defaults={'stock_actual': Decimal(str(rng.randint(30, 120)))},
                )

        ingresos_totales = total_ingresos_ventas + total_ingresos_pedidos
        egresos_totales = total_gastado_mp + total_gastos_op + total_inversiones
        resultado_neto = ingresos_totales - egresos_totales
        utilidad_operativa = ingresos_totales - total_gastado_mp - total_gastos_op

        self.stdout.write(self.style.SUCCESS(
            f'\nRESULTADOS DE {nombre_mes.upper()} 2026:\n'
            f'  - Jornadas de producción: {total_producciones_creadas} lotes diarios\n'
            f'  - Ventas en mostrador (35-40/día): {total_ventas_creadas} transacciones (Bs {total_ingresos_ventas:,.2f})\n'
            f'  - Pedidos anticipados: {total_pedidos_creados} pedidos (Bs {total_ingresos_pedidos:,.2f})\n'
            f'  - INGRESOS TOTALES: Bs {ingresos_totales:,.2f}\n'
            f'  - Compras materia prima: Bs {total_gastado_mp:,.2f} ({total_compras_creadas} compras)\n'
            f'  - Gastos operativos: Bs {total_gastos_op:,.2f}\n'
            f'  - Inversiones (CAPEX): Bs {total_inversiones:,.2f}\n'
            f'  - EGRESOS TOTALES: Bs {egresos_totales:,.2f}\n'
            f'  --------------------------------------------------------\n'
            f'  - UTILIDAD OPERATIVA: +Bs {utilidad_operativa:,.2f}\n'
            f'  - RESULTADO NETO FINAL: +Bs {resultado_neto:,.2f} (SUPERÁVIT POSITIVO)\n'
        ))
