from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.produccion.models import DetalleProduccion, Produccion
from apps.productos_inventario.productos_terminados.models import NotaPerdidaProducto


DETALLES_DEMO = [
    ('Marraqueta', 200),
    ('Casero', 100),
    ('Tortilla', 30),
    ('Arani', 80),
    ('Chama', 60),
    ('Integral', 50),
    ('Pan Dulce', 60),
    ('Pan con Azúcar', 50),
    ('Gusanito', 40),
    ('Pan Mollete', 70),
    ('Pan Galleta', 90),
    ('Pan de Leche', 40),
]

JORNADAS_DEMO = [
    ('2026-09-06', 'Mañana', 'mrojas'),
    ('2026-09-07', 'Tarde', 'mrojas'),
    ('2026-09-08', 'Noche', 'ptorrez'),
    ('2026-09-09', 'Mañana', 'mrojas'),
]


class Command(BaseCommand):
    help = 'Carga las jornadas de demostración de los 4 días (CU10 & CU11) y mermas (CU18).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Valida dependencias e informa qué se cargaría, sin guardar registros.',
        )

    def handle(self, *args, **options):
        if Produccion.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {Produccion.objects.count()} producciones en esta base. No se cargaron datos demo para evitar mezclarlos.'
                )
            )
            return

        Usuario = get_user_model()
        usuarios = {
            usuario.nombre_usuario: usuario
            for usuario in Usuario.objects.filter(
                nombre_usuario__in={fila[2] for fila in JORNADAS_DEMO}
            )
        }
        productos = {
            producto.nombre: producto
            for producto in Producto.objects.filter(
                nombre__in={nombre for nombre, _ in DETALLES_DEMO}
            )
        }

        usuarios_faltantes = sorted({fila[2] for fila in JORNADAS_DEMO} - usuarios.keys())
        productos_faltantes = sorted({nombre for nombre, _ in DETALLES_DEMO} - productos.keys())
        if usuarios_faltantes or productos_faltantes:
            faltantes = []
            if usuarios_faltantes:
                faltantes.append(f'usuarios: {", ".join(usuarios_faltantes)}')
            if productos_faltantes:
                faltantes.append(f'productos: {", ".join(productos_faltantes)}')
            self.stdout.write(
                self.style.ERROR(f'Faltan datos requeridos para el demo ({"; ".join(faltantes)}). Ejecuta seed_usuarios y seed_productos primero.')
            )
            return

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Demo validado: se crearían {len(JORNADAS_DEMO)} jornadas y '
                    f'{len(JORNADAS_DEMO) * len(DETALLES_DEMO)} detalles. No se guardó nada.'
                )
            )
            return

        with transaction.atomic():
            detalles_creados = []
            for fecha, jornada, nombre_usuario in JORNADAS_DEMO:
                produccion = Produccion.objects.create(
                    fecha=date.fromisoformat(fecha),
                    jornada=jornada,
                    id_usuario=usuarios[nombre_usuario],
                )
                for nombre_producto, cantidad in DETALLES_DEMO:
                    prod = productos[nombre_producto]
                    det = DetalleProduccion.objects.create(
                        id_produccion=produccion,
                        id_producto=prod,
                        cantidad_producida=cantidad,
                        costo_unitario=prod.costo_produccion,
                    )
                    detalles_creados.append(det)

            # Mermas demo según Poblacion_4_Dias_Panaderia_Santiago.sql
            # 1. 3 Panes Dulces dañados en Día 1
            # 2. 5 Marraquetas dañadas en Día 2
            usuario_mrojas = usuarios.get('mrojas')
            if usuario_mrojas and len(detalles_creados) >= 15:
                # Buscar pan dulce del dia 1
                det_pan_dulce_d1 = next(
                    (d for d in detalles_creados if d.id_produccion.fecha == date(2026, 9, 6) and d.id_producto.nombre == 'Pan Dulce'),
                    None
                )
                if det_pan_dulce_d1:
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=det_pan_dulce_d1,
                        id_usuario=usuario_mrojas,
                        cantidad=3,
                        costo_unitario=det_pan_dulce_d1.costo_unitario,
                        fecha_salida=timezone.make_aware(datetime(2026, 9, 6, 20, 0, 0)),
                    )

                # Buscar marraqueta del dia 2
                det_marraqueta_d2 = next(
                    (d for d in detalles_creados if d.id_produccion.fecha == date(2026, 9, 7) and d.id_producto.nombre == 'Marraqueta'),
                    None
                )
                if det_marraqueta_d2:
                    NotaPerdidaProducto.objects.create(
                        id_detalle_produccion=det_marraqueta_d2,
                        id_usuario=usuario_mrojas,
                        cantidad=5,
                        costo_unitario=det_marraqueta_d2.costo_unitario,
                        fecha_salida=timezone.make_aware(datetime(2026, 9, 7, 20, 0, 0)),
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Se cargaron {len(JORNADAS_DEMO)} jornadas demo con '
                f'{len(detalles_creados)} detalles y sus notas de pérdida (mermas).'
            )
        )
