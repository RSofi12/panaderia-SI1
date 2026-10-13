from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.produccion.models import DetalleProduccion, Produccion


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
]


class Command(BaseCommand):
    help = 'Carga tres jornadas de demostración para revisar el CU11; no modifica inventarios.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Valida dependencias e informa qué se cargaría, sin guardar registros.',
        )

    def handle(self, *args, **options):
        if Produccion.objects.exists():
            raise CommandError(
                'Ya existen producciones en esta base. No se cargaron datos demo para evitar mezclarlos.'
            )

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
            raise CommandError(f'Faltan datos requeridos para el demo ({"; ".join(faltantes)}).')

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Demo validado: se crearían {len(JORNADAS_DEMO)} jornadas y '
                    f'{len(JORNADAS_DEMO) * len(DETALLES_DEMO)} detalles. No se guardó nada.'
                )
            )
            return

        with transaction.atomic():
            for fecha, jornada, nombre_usuario in JORNADAS_DEMO:
                produccion = Produccion.objects.create(
                    fecha=date.fromisoformat(fecha),
                    jornada=jornada,
                    id_usuario=usuarios[nombre_usuario],
                )
                DetalleProduccion.objects.bulk_create([
                    DetalleProduccion(
                        id_produccion=produccion,
                        id_producto=productos[nombre_producto],
                        cantidad_producida=cantidad,
                        costo_unitario=productos[nombre_producto].costo_produccion,
                    )
                    for nombre_producto, cantidad in DETALLES_DEMO
                ])

        self.stdout.write(
            self.style.SUCCESS(
                f'Se cargaron {len(JORNADAS_DEMO)} jornadas demo con '
                f'{len(JORNADAS_DEMO) * len(DETALLES_DEMO)} detalles. '
                'No se modificaron existencias ni movimientos de inventario.'
            )
        )