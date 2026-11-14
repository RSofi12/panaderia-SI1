"""
Comando de Poblado para 1 Mes Operativo Completo — Panadería Santiago (SI-1).

Simula 1 mes de operación comercial y productiva continua (Octubre 2026):
- 27 jornadas laborales (Lunes a Sábado, descanso dominical).
- Horario comercial convencional de 8 horas (06:30 a 14:30).
- Ventas en mostrador: 22 a 28 entre semana, 15 a 20 los sábados.
- Producción diaria madrugadora (05:00 a 07:00) cubriendo 36 variedades.
- Mermas de producto terminado periódicas.
- Compras semanales recurrentes a los 9 proveedores.
- Pedidos anticipados de clientes frecuentes con entregas cumplidas.
- Gastos fijos y variables del mes (alquiler, luz, agua, mantenimiento, insumos).

Uso:
    python manage.py seed_mes_operativo
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
    help = 'Puebla 1 mes completo (Octubre 2026) de trabajo continuo para Panadería Santiago.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecuta la población incluso si ya existen registros de octubre de 2026.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIME(
            '============================================================\n'
            '  INICIANDO POBLADO DE 1 MES OPERATIVO (OCTUBRE 2026)       \n'
            '============================================================'
        ) if hasattr(self.style, 'MIME') else self.style.NOTICE(
            '============================================================\n'
            '  INICIANDO POBLADO DE 1 MES OPERATIVO (OCTUBRE 2026)       \n'
            '============================================================'
        ))

        # 1. Validar prerrequisitos (Usuarios, Productos, Proveedores, Materias Primas)
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
            # Crear clientes por defecto si no existen
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

        # 2. Verificar si ya se pobló octubre
        ya_poblado = Venta.objects.filter(
            fecha_hora__year=2026, fecha_hora__month=10, id_transaccion_stripe__startswith='pi_mes_oct_'
        ).exists()

        if ya_poblado and not options.get('force'):
            self.stdout.write(self.style.WARNING(
                'Ya existen ventas del mes operativo de Octubre 2026. '
                'Use --force si desea regenerar o añadir datos.'
            ))
            return

        # Generador con semilla determinista para consistencia
        rng = random.Random(202610)

        # Obtener siguiente número de comprobante único
        max_comp = Venta.objects.aggregate(m=Max('numero_comprobante'))['m'] or 1000
        numero_comprobante_actual = max(max_comp + 1, 20000)

        dias_operativos = []
        fecha_cursor = date(2026, 10, 1)
        fecha_fin = date(2026, 10, 31)

        while fecha_cursor <= fecha_fin:
            # 0=Lunes, 1=Martes, ..., 5=Sábado, 6=Domingo
            if fecha_cursor.weekday() < 6:  # Lunes a Sábado
                dias_operativos.append(fecha_cursor)
            fecha_cursor += timedelta(days=1)

        self.stdout.write(f'Procesando {len(dias_operativos)} días hábiles en Octubre de 2026...')

        total_ventas_creadas = 0
        total_detalles_ventas = 0
        total_ingresos_bs = Decimal('0.00')

        total_producciones_creadas = 0
        total_detalles_produccion = 0

        total_compras_creadas = 0
        total_detalles_compras = 0

        total_pedidos_creados = 0
        total_gastos_creados = 0

        # Mapeos útiles de productos
        prod_por_nombre = {p.nombre: p for p in productos}
        panes_tradicionales = [p for p in productos if p.id_categoria.nombre == 'Panes Tradicionales']
        masas_tipicas = [p for p in productos if p.id_categoria.nombre == 'Masas Típicas Cruceñas']
        salados = [p for p in productos if p.id_categoria.nombre == 'Salados y Especialidades']
        reposteria = [p for p in productos if p.id_categoria.nombre == 'Repostería y Queques']
        gourmet = [p for p in productos if p.id_categoria.nombre in ('Panadería Gourmet y Rústica', 'Panes Integrales')]

        with transaction.atomic():
            # =========================================================
            # A. COMPRAS SEMANALES RECURRENTES DE MATERIA PRIMA (16 compras)
            # =========================================================
            dias_compras = [
                (date(2026, 10, 2), proveedores[0 % len(proveedores)]),
                (date(2026, 10, 2), proveedores[1 % len(proveedores)]),
                (date(2026, 10, 5), proveedores[2 % len(proveedores)]),
                (date(2026, 10, 7), proveedores[3 % len(proveedores)]),
                (date(2026, 10, 9), proveedores[4 % len(proveedores)]),
                (date(2026, 10, 12), proveedores[5 % len(proveedores)]),
                (date(2026, 10, 14), proveedores[6 % len(proveedores)]),
                (date(2026, 10, 16), proveedores[0 % len(proveedores)]),
                (date(2026, 10, 19), proveedores[1 % len(proveedores)]),
                (date(2026, 10, 21), proveedores[7 % len(proveedores)]),
                (date(2026, 10, 23), proveedores[8 % len(proveedores)]),
                (date(2026, 10, 26), proveedores[2 % len(proveedores)]),
                (date(2026, 10, 28), proveedores[3 % len(proveedores)]),
                (date(2026, 10, 30), proveedores[0 % len(proveedores)]),
                (date(2026, 10, 30), proveedores[1 % len(proveedores)]),
                (date(2026, 10, 31), proveedores[5 % len(proveedores)]),
            ]

            for f_compra, prov in dias_compras:
                dt_compra = timezone.make_aware(datetime.combine(f_compra, time(8, 30)))
                compra = Compra.objects.create(
                    id_proveedor=prov,
                    id_usuario=admin_user,
                    fecha_hora=dt_compra,
                    total=Decimal('0.00'),
                )
                total_compras_creadas += 1

                # 3 a 5 materias primas por compra
                items_mp = rng.sample(materias, k=min(4, len(materias)))
                total_c = Decimal('0.00')
                for mp in items_mp:
                    cant = Decimal(str(rng.randint(30, 150)))
                    # Precio unitario estimado
                    p_unit = Decimal(str(rng.choice([4.50, 6.00, 32.00, 18.00, 24.00, 7.50, 35.00])))
                    subt = (cant * p_unit).quantize(Decimal('0.01'))
                    DetalleCompra.objects.create(
                        id_compra=compra,
                        id_materia_prima=mp,
                        cantidad=cant,
                        precio_unitario=p_unit,
                        subtotal=subt,
                    )
                    total_c += subt
                    total_detalles_compras += 1

                compra.total = total_c
                compra.save(update_fields=['total'])

            # =========================================================
            # B. JORNADAS DE PRODUCCIÓN, VENTAS Y PEDIDOS DIARIOS
            # =========================================================
            for dia in dias_operativos:
                es_sabado = (dia.weekday() == 5)
                panadero = rng.choice(panaderos)
                cajera = rng.choice(cajeras)

                # 1. Producción diaria (05:15 am)
                prod = Produccion.objects.create(
                    id_usuario=panadero,
                    fecha=dia,
                    jornada=JornadaProduccion.MANANA,
                )
                total_producciones_creadas += 1

                # Detalle de producción para 20 a 28 productos por jornada
                prods_jornada = rng.sample(productos, k=rng.randint(20, min(28, len(productos))))
                detalles_prod_creados = []
                for p in prods_jornada:
                    # Cantidad producida según tipo
                    if p in panes_tradicionales:
                        cant_p = rng.randint(150, 300)
                    elif p in masas_tipicas:
                        cant_p = rng.randint(40, 90)
                    elif p in salados:
                        cant_p = rng.randint(35, 70)
                    elif p in reposteria:
                        cant_p = rng.randint(15, 40)
                    else:
                        cant_p = rng.randint(25, 60)

                    dp = DetalleProduccion.objects.create(
                        id_produccion=prod,
                        id_producto=p,
                        cantidad_producida=cant_p,
                    )
                    detalles_prod_creados.append(dp)
                    total_detalles_produccion += 1

                # Merma ocasional (cada 3 días, 1 o 2 notas de pérdida)
                if dia.day % 3 == 0 and detalles_prod_creados:
                    dp_merma = rng.choice(detalles_prod_creados)
                    cant_merma = rng.randint(2, 6)
                    cu_merma = dp_merma.id_producto.costo_produccion
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=dp_merma,
                        id_usuario=panadero,
                        cantidad=cant_merma,
                        costo_unitario=cu_merma,
                        fecha_salida=timezone.make_aware(datetime.combine(dia, time(14, 0))),
                    )

                # 2. Ventas en mostrador (06:30 a 14:30)
                # Sábados: 15 a 20 ventas. Entre semana: 22 a 28 ventas.
                num_ventas = rng.randint(15, 20) if es_sabado else rng.randint(22, 28)

                minutos_disponibles = 480  # 8 horas = 480 minutos
                # Generar minutos ordenados en el día
                minutos_ventas = sorted(rng.sample(range(0, minutos_disponibles), k=num_ventas))

                for m in minutos_ventas:
                    hora_venta = time(6, 30)
                    dt_venta = timezone.make_aware(
                        datetime.combine(dia, time(6, 30)) + timedelta(minutes=m)
                    )

                    # 75% efectivo, 25% stripe
                    es_stripe = (rng.random() < 0.25)
                    metodo = MetodoPago.STRIPE if es_stripe else MetodoPago.EFECTIVO
                    stripe_id = f'pi_mes_oct_{numero_comprobante_actual}' if es_stripe else None

                    venta = Venta.objects.create(
                        id_usuario=cajera,
                        numero_comprobante=numero_comprobante_actual,
                        fecha_hora=dt_venta,
                        metodo_pago=metodo,
                        id_transaccion_stripe=stripe_id,
                        total=Decimal('0.00'),
                    )
                    numero_comprobante_actual += 1
                    total_ventas_creadas += 1

                    # 1 a 4 productos por ticket
                    n_lineas = rng.choices([1, 2, 3, 4], weights=[40, 35, 18, 7])[0]
                    prods_ticket = rng.sample(productos, k=min(n_lineas, len(productos)))

                    total_v = Decimal('0.00')
                    for prod_sel in prods_ticket:
                        if prod_sel in panes_tradicionales:
                            cant_v = rng.randint(6, 25)
                        elif prod_sel in masas_tipicas:
                            cant_v = rng.randint(2, 8)
                        elif prod_sel in salados:
                            cant_v = rng.randint(1, 4)
                        elif prod_sel in reposteria:
                            cant_v = rng.randint(1, 3)
                        else:
                            cant_v = rng.randint(2, 6)

                        pu = prod_sel.precio_venta
                        subt = (pu * cant_v).quantize(Decimal('0.01'))

                        DetalleVenta.objects.create(
                            id_venta=venta,
                            id_producto=prod_sel,
                            cantidad=cant_v,
                            precio_unitario=pu,
                            subtotal=subt,
                        )
                        total_v += subt
                        total_detalles_ventas += 1

                    venta.total = total_v
                    venta.save(update_fields=['total'])
                    total_ingresos_bs += total_v

                # 3. Pedidos anticipados de clientes (1 a 2 por día)
                if rng.random() < 0.70:
                    cliente_sel = rng.choice(clientes)
                    hora_reg = time(7, 30)
                    hora_ent = time(rng.randint(9, 14), 0)
                    dt_reg = timezone.make_aware(datetime.combine(dia, hora_reg))
                    dt_ent = timezone.make_aware(datetime.combine(dia, hora_ent))

                    ped_stripe = (rng.random() < 0.35)
                    metodo_ped = MetodoPago.STRIPE if ped_stripe else MetodoPago.EFECTIVO
                    stripe_ped_id = f'pi_mes_oct_ped_{numero_comprobante_actual}' if ped_stripe else None

                    pedido = Pedido.objects.create(
                        id_cliente=cliente_sel,
                        id_usuario=cajera,
                        fecha_registro=dt_reg,
                        fecha_entrega=dt_ent,
                        estado=EstadoPedido.ENTREGADO,
                        metodo_pago=metodo_ped,
                        id_transaccion_stripe=stripe_ped_id,
                        pagado=True,
                        total=Decimal('0.00'),
                    )
                    total_pedidos_creados += 1

                    prods_ped = rng.sample(productos, k=rng.randint(2, 4))
                    total_p = Decimal('0.00')
                    for p_sel in prods_ped:
                        cant_ped = rng.randint(15, 50)
                        pu_ped = p_sel.precio_venta
                        subt_ped = (pu_ped * cant_ped).quantize(Decimal('0.01'))
                        DetallePedido.objects.create(
                            id_pedido=pedido,
                            id_producto=p_sel,
                            cantidad=cant_ped,
                            precio_unitario=pu_ped,
                            subtotal=subt_ped,
                        )
                        total_p += subt_ped

                    pedido.total = total_p
                    pedido.save(update_fields=['total'])

            # =========================================================
            # C. GASTOS E INVERSIONES DEL MES (CU20)
            # =========================================================
            gastos_octubre = [
                (date(2026, 10, 2), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.ALQUILER, 'Alquiler mensual del local comercial', 'Pago mensual al arrendador del inmueble en calle comercial', Decimal('2800.00')),
                (date(2026, 10, 8), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Energía Eléctrica CRE', 'Factura de luz trifásica para hornos rotativos y cámaras', Decimal('1450.00')),
                (date(2026, 10, 10), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.SERVICIOS, 'Agua potable SAGUAPAC', 'Consumo mensual de agua potable para producción e higiene', Decimal('320.00')),
                (date(2026, 10, 15), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.MANTENIMIENTO, 'Mantenimiento preventivo de hornos y amasadora', 'Lubricación de rodamientos, revisión de quemadores a gas y correas', Decimal('650.00')),
                (date(2026, 10, 22), TipoMovimientoEconomico.INVERSION, CategoriaMovimientoEconomico.EQUIPOS, 'Bandejas de acero y canastas de mostrador', 'Inversión en 15 bandejas perforadas para baguette y canastas artesanales', Decimal('580.00')),
                (date(2026, 10, 29), TipoMovimientoEconomico.GASTO, CategoriaMovimientoEconomico.OTROS, 'Artículos de desinfección y limpieza industrial', 'Detergentes grado alimenticio, toallas y alcohol para higiene', Decimal('220.00')),
            ]

            for f_gasto, tipo_g, cat_g, conc_g, desc_g, monto_g in gastos_octubre:
                MovimientoEconomico.objects.create(
                    id_usuario=admin_user,
                    tipo=tipo_g,
                    categoria=cat_g,
                    concepto=conc_g,
                    descripcion=desc_g,
                    monto=monto_g,
                    fecha_hora=timezone.make_aware(datetime.combine(f_gasto, time(10, 0))),
                )
                total_gastos_creados += 1

            # =========================================================
            # D. AJUSTE DE EXISTENCIAS FINALES SALUDABLES (CU12)
            # =========================================================
            for p in productos:
                stock_saludable = rng.randint(40, 160)
                InventarioProductoTerminado.objects.update_or_create(
                    id_producto=p,
                    defaults={'stock_actual': stock_saludable},
                )

            for m in materias:
                stock_mp_saludable = Decimal(str(rng.randint(25, 120)))
                InventarioMateriaPrima.objects.update_or_create(
                    id_materia_prima=m,
                    defaults={'stock_actual': stock_mp_saludable},
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nPOBLADO DE MES OPERATIVO COMPLETADO EXITOSAMENTE:\n'
            f' - Días hábiles simulados: {len(dias_operativos)} jornadas (Lunes a Sábado, 8 horas diarias)\n'
            f' - Ventas en mostrador creadas: {total_ventas_creadas} tickets\n'
            f' - Líneas de detalle venta: {total_detalles_ventas} registros\n'
            f' - Ingresos totales facturados en el mes: Bs {total_ingresos_bs:,.2f}\n'
            f' - Jornadas de producción: {total_producciones_creadas} lotes ({total_detalles_produccion} líneas)\n'
            f' - Compras de materia prima: {total_compras_creadas} compras ({total_detalles_compras} líneas)\n'
            f' - Pedidos anticipados de clientes: {total_pedidos_creados} pedidos\n'
            f' - Gastos e inversiones del mes: {total_gastos_creados} movimientos (Bs 6,020.00)\n'
        ))
