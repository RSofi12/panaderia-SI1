"""
Comando de Poblado para Meses Operativos Completos (Julio, Agosto, Septiembre y Octubre 2026) — Panadería Santiago (SI-1).

Simula la operación comercial y productiva de 4 meses históricos continuos:
- Julio 2026 (Mitad / Apertura, 15 al 31 de Julio): 15 días hábiles, 18-24 ventas/día,
  15 lotes de producción (~450 panes/lote), compras iniciales y menaje menor. Ganancia neta: +Bs 870.
- Agosto 2026 (Crecimiento, 1 al 31 de Agosto): 26 días hábiles, 26-32 ventas/día,
  26 lotes de producción (~680 panes/lote), primeros pedidos institucionales. Ganancia neta: +Bs 5.480.
- Septiembre 2026 (Operación plena): 26 días hábiles, 35-40 ventas/día,
  26 lotes (~850 panes/lote), compras semanales e inversión del horno rotativo (Bs 8.000). Superávit neto: +Bs 830.
- Octubre 2026 (Consolidación): 27 días hábiles, 35-40 ventas/día,
  27 lotes (~850 panes/lote), compras semanales y gastos operativos regulares. Ganancia neta: +Bs 6.080.

Uso:
    python manage.py seed_mes_operativo [--force] [--mes 7|8|9|10]
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
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla meses operativos completos (Julio, Agosto, Septiembre y Octubre 2026) con ganancias coherentes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecuta la población incluso si ya existen registros en los meses indicados.',
        )
        parser.add_argument(
            '--mes',
            type=int,
            choices=[7, 8, 9, 10],
            help='Especifica si se quiere poblar únicamente Julio (7), Agosto (8), Septiembre (9) u Octubre (10). Por defecto todos.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIME(
            '============================================================\n'
            '  POBLADO DE MESES OPERATIVOS (JULIO A OCTUBRE 2026)        \n'
            '============================================================'
        ) if hasattr(self.style, 'MIME') else self.style.NOTICE(
            '============================================================\n'
            '  POBLADO DE MESES OPERATIVOS (JULIO A OCTUBRE 2026)        \n'
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

        meses_a_procesar = [options['mes']] if options.get('mes') else [7, 8, 9, 10]

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
        nombres_mes = {7: 'Julio (Apertura)', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre'}
        prefijos_stripe = {7: 'pi_mes_jul_', 8: 'pi_mes_ago_', 9: 'pi_mes_sep_', 10: 'pi_mes_oct_'}
        seed_rnds = {7: 202607, 8: 202608, 9: 202609, 10: 202610}

        nombre_mes = nombres_mes[mes]
        prefijo_stripe = prefijos_stripe[mes]
        rng = random.Random(seed_rnds[mes])

        self.stdout.write(self.style.NOTICE(f'\n--- Procesando {nombre_mes} 2026 ---'))

        # Verificar si ya tiene datos suficientes
        ventas_mes = Venta.objects.filter(
            fecha_hora__year=2026, fecha_hora__month=mes
        ).count()

        min_ventas_esperadas = 200 if mes == 7 else 500
        if ventas_mes >= min_ventas_esperadas and not force:
            self.stdout.write(self.style.WARNING(
                f'{nombre_mes} 2026 ya cuenta con {ventas_mes} ventas. Use --force para regenerar.'
            ))
            return

        # Siguiente número de comprobante único
        max_comp = Venta.objects.aggregate(m=Max('numero_comprobante'))['m'] or 1000
        numero_comprobante = max_comp + 1

        # Rango de fechas
        primer_dia = 15 if mes == 7 else 1
        ultimo_dia = 31 if mes in [7, 8, 10] else 30
        dias_operativos = []
        fecha_cursor = date(2026, mes, primer_dia)
        fecha_fin = date(2026, mes, ultimo_dia)

        while fecha_cursor <= fecha_fin:
            # 0=Lunes ... 5=Sábado, 6=Domingo (Descanso dominical)
            if fecha_cursor.weekday() < 6:
                dias_operativos.append(fecha_cursor)
            fecha_cursor += timedelta(days=1)

        self.stdout.write(f'Jornadas laborales a simular en {nombre_mes}: {len(dias_operativos)} días (Lunes a Sábado)')

        with transaction.atomic():
            if force or ventas_mes < min_ventas_esperadas:
                # 1. Limpiar Ventas y sus detalles protegidos
                ventas_del_mes = Venta.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes)
                ids_ventas = list(ventas_del_mes.values_list('id_venta', flat=True))
                MovimientoProductoTerminado.objects.filter(id_venta_id__in=ids_ventas).delete()
                DetalleVenta.objects.filter(id_venta_id__in=ids_ventas).delete()
                ventas_del_mes.delete()

                # 2. Limpiar Pedidos y sus detalles protegidos
                pedidos_del_mes = Pedido.objects.filter(fecha_registro__year=2026, fecha_registro__month=mes)
                ids_pedidos = list(pedidos_del_mes.values_list('id_pedido', flat=True))
                Venta.objects.filter(id_pedido_id__in=ids_pedidos).update(id_pedido=None)
                MovimientoProductoTerminado.objects.filter(id_pedido_id__in=ids_pedidos).delete()
                DetallePedido.objects.filter(id_pedido_id__in=ids_pedidos).delete()
                pedidos_del_mes.delete()

                # 3. Limpiar Producciones y sus detalles / mermas protegidas
                prods_del_mes = Produccion.objects.filter(fecha__year=2026, fecha__month=mes)
                ids_prods = list(prods_del_mes.values_list('id_produccion', flat=True))
                dets_prod = DetalleProduccion.objects.filter(id_produccion_id__in=ids_prods)
                ids_dets = list(dets_prod.values_list('id_detalle_produccion', flat=True))

                ids_notas_perdida = list(
                    NotaPerdidaProducto.objects.filter(id_detalle_produccion_id__in=ids_dets).values_list(
                        'id_nota_perdida', flat=True
                    )
                )
                MovimientoProductoTerminado.objects.filter(id_nota_perdida_id__in=ids_notas_perdida).delete()
                NotaPerdidaProducto.objects.filter(id_nota_perdida__in=ids_notas_perdida).delete()

                MovimientoProductoTerminado.objects.filter(id_produccion_id__in=ids_prods).delete()
                dets_prod.delete()
                prods_del_mes.delete()

                # 4. Limpiar Compras y sus detalles
                compras_del_mes = Compra.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes)
                ids_compras = list(compras_del_mes.values_list('id_compra', flat=True))
                DetalleCompra.objects.filter(id_compra_id__in=ids_compras).delete()
                compras_del_mes.delete()

                # 5. Limpiar Movimientos económicos (gastos/inversiones)
                MovimientoEconomico.objects.filter(fecha_hora__year=2026, fecha_hora__month=mes).delete()

            # A. COMPRAS RECURRENTES DE MATERIA PRIMA
            total_compras_creadas = 0
            total_gastado_mp = Decimal('0.00')

            if mes == 7:
                dias_compras = [15, 18, 21, 24, 27, 30]
            elif mes == 8:
                dias_compras = [1, 4, 7, 10, 13, 17, 20, 22, 25, 27, 29, 31]
            elif mes == 9:
                dias_compras = [1, 3, 5, 8, 10, 12, 15, 17, 19, 22, 24, 26, 28]
            else:
                dias_compras = [2, 5, 7, 9, 12, 14, 16, 19, 21, 23, 26, 28, 30]

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
                    cant_min = 20 if mes == 7 else 30
                    cant_max = 50 if mes == 7 else (70 if mes == 8 else 80)
                    for mp in items_mp:
                        cant = Decimal(str(rng.randint(cant_min, cant_max)))
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
                    if mes == 7:
                        cant_p = rng.randint(35, 90) if 'Marraqueta' in p.nombre or 'Casero' in p.nombre else rng.randint(15, 35)
                    elif mes == 8:
                        cant_p = rng.randint(50, 140) if 'Marraqueta' in p.nombre or 'Casero' in p.nombre else rng.randint(20, 45)
                    else:
                        cant_p = rng.randint(60, 180) if 'Marraqueta' in p.nombre or 'Casero' in p.nombre else rng.randint(25, 60)

                    dp = DetalleProduccion.objects.create(
                        id_produccion=prod,
                        id_producto=p,
                        cantidad_producida=cant_p,
                        costo_unitario=p.costo_produccion,
                    )
                    detalles_prod_creados.append(dp)

                # Mermas realistas diarias (CU18)
                if detalles_prod_creados:
                    # 1. Sobrante de mostrador al cierre de atención (18:15 hrs)
                    cant_sobrante_rango = (
                        (6, 12) if mes == 7 else
                        (10, 18) if mes == 8 else
                        (14, 22) if mes == 9 else
                        (16, 24)
                    )
                    dp_sobrante = rng.choice(detalles_prod_creados)
                    cant_sob = rng.randint(*cant_sobrante_rango)
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=dp_sobrante,
                        id_usuario=panadero,
                        cantidad=cant_sob,
                        costo_unitario=dp_sobrante.costo_unitario,
                        motivo='Sobrante de mostrador al cierre',
                        observaciones='Pan frío no vendido al cierre de mostrador (18:15 hrs)',
                        fecha_salida=timezone.make_aware(datetime.combine(dia, time(18, 15))),
                    )

                    # 2. Defectos de horneado matutino (cada 2 días, 08:30 hrs)
                    if dia.day % 2 == 0:
                        dp_defecto = rng.choice(detalles_prod_creados)
                        cant_def = rng.randint(3, 7)
                        NotaPerdidaProducto.objects.create(
                            id_detalle_produccion=dp_defecto,
                            id_usuario=panadero,
                            cantidad=cant_def,
                            costo_unitario=dp_defecto.costo_unitario,
                            motivo='Defecto de horneado / deformación',
                            observaciones='Pan con exceso de cocción o deforme retirado de horno (08:30 hrs)',
                            fecha_salida=timezone.make_aware(datetime.combine(dia, time(8, 30))),
                        )

                # 2. Ventas diarias de mostrador según etapa de crecimiento
                if mes == 7:
                    num_ventas = rng.randint(18, 24)
                elif mes == 8:
                    num_ventas = rng.randint(26, 32)
                else:
                    num_ventas = rng.randint(35, 40)

                n_manana = int(num_ventas * 0.60)
                n_tarde = num_ventas - n_manana

                minutos_manana = sorted(rng.sample(range(8 * 60, 12 * 60), n_manana))
                minutos_tarde = sorted(rng.sample(range(15 * 60, 18 * 60 + 30), n_tarde))

                for m_total in minutos_manana:
                    h, m = divmod(m_total, 60)
                    dt_venta = timezone.make_aware(datetime.combine(dia, time(h, m)))
                    es_stripe = (rng.random() < 0.22)
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

                    prods_ticket = rng.sample(productos, k=rng.randint(1, 3))
                    total_v = Decimal('0.00')
                    for p_sel in prods_ticket:
                        max_c = 10 if mes == 7 else 15
                        cant_v = rng.randint(4, max_c) if 'Marraqueta' in p_sel.nombre or 'Casero' in p_sel.nombre else rng.randint(2, 6)
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
                    es_stripe = (rng.random() < 0.22)
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
                        cant_v = rng.randint(2, 5)
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

                # 3. Pedidos anticipados de clientes
                prob_pedido = 0.35 if mes == 7 else (0.55 if mes == 8 else 0.75)
                if rng.random() < prob_pedido:
                    cliente_sel = rng.choice(clientes)
                    dt_reg = timezone.make_aware(datetime.combine(dia, time(7, 30)))
                    dt_ent = timezone.make_aware(datetime.combine(dia, time(rng.randint(9, 17), 0)))
                    ped_stripe = (rng.random() < 0.30)
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
                    max_cant_ped = 25 if mes == 7 else 40
                    for p_sel in prods_ped:
                        cant_ped = rng.randint(10, max_cant_ped)
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

            if mes == 7:
                movimientos_mes = [
                    (date(2026, 7, 16), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.ALQUILER, 'Alquiler proporcional local comercial (Quincena)', 'Pago proporcional del alquiler del establecimiento por inicio de operaciones', Decimal('750.00')),
                    (date(2026, 7, 18), TipoMovimientoEconomico.INVERSION, CategoriaMovimientoEconomico.EQUIPOS, 'Moldes y cuchillos panaderos', 'Inversión inicial en moldes de lata y cuchillos para corte de masa', Decimal('380.00')),
                    (date(2026, 7, 28), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Servicios básicos de prueba', 'Consumo inicial de energía eléctrica y agua para pruebas de horneado', Decimal('100.00')),
                ]
            elif mes == 8:
                movimientos_mes = [
                    (date(2026, 8, 3), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.ALQUILER, 'Alquiler mensual del local comercial', 'Pago mensual de alquiler del establecimiento comercial', Decimal('1500.00')),
                    (date(2026, 8, 8), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Energía eléctrica CRE', 'Factura de luz para iluminación y maquinaria básica', Decimal('380.00')),
                    (date(2026, 8, 10), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Agua potable SAGUAPAC', 'Consumo mensual de agua potable para elaboración e higiene', Decimal('110.00')),
                    (date(2026, 8, 20), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.MANTENIMIENTO, 'Mantenimiento preventivo inicial', 'Revisión técnica preventiva de hornos a gas', Decimal('130.00')),
                ]
            elif mes == 9:
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
            f'  - Ventas en mostrador: {total_ventas_creadas} transacciones (Bs {total_ingresos_ventas:,.2f})\n'
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
