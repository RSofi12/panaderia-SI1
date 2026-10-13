from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.productos.models import Producto, ProductoMateriaPrima

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql (§ 2. MÓDULO PRODUCTOS - Recetas BOM / MRP)
RECETAS = [
    # 1. Marraqueta
    ('Marraqueta', 'Harina', '0.060', 'kg'),
    ('Marraqueta', 'Levadura', '0.002', 'kg'),
    ('Marraqueta', 'Sal', '0.001', 'kg'),
    # 2. Casero
    ('Casero', 'Harina', '0.070', 'kg'),
    ('Casero', 'Levadura', '0.002', 'kg'),
    ('Casero', 'Sal', '0.001', 'kg'),
    # 3. Tortilla
    ('Tortilla', 'Harina', '0.150', 'kg'),
    ('Tortilla', 'Levadura', '0.003', 'kg'),
    ('Tortilla', 'Sal', '0.002', 'kg'),
    ('Tortilla', 'Leche', '0.020', 'litro'),
    # 4. Arani
    ('Arani', 'Harina', '0.080', 'kg'),
    ('Arani', 'Levadura', '0.002', 'kg'),
    ('Arani', 'Azúcar', '0.010', 'kg'),
    # 5. Chama
    ('Chama', 'Harina', '0.080', 'kg'),
    ('Chama', 'Levadura', '0.002', 'kg'),
    ('Chama', 'Azúcar', '0.015', 'kg'),
    # 6. Integral
    ('Integral', 'Harina', '0.070', 'kg'),
    ('Integral', 'Levadura', '0.002', 'kg'),
    ('Integral', 'Sal', '0.001', 'kg'),
    # 7. Pan Dulce
    ('Pan Dulce', 'Harina', '0.060', 'kg'),
    ('Pan Dulce', 'Azúcar', '0.020', 'kg'),
    ('Pan Dulce', 'Huevos', '0.050', 'unidad'),
    ('Pan Dulce', 'Mantequilla', '0.010', 'kg'),
    # 8. Pan con Azúcar
    ('Pan con Azúcar', 'Harina', '0.060', 'kg'),
    ('Pan con Azúcar', 'Azúcar', '0.025', 'kg'),
    # 9. Gusanito
    ('Gusanito', 'Harina', '0.090', 'kg'),
    ('Gusanito', 'Azúcar', '0.020', 'kg'),
    ('Gusanito', 'Mantequilla', '0.015', 'kg'),
    # 10. Pan Mollete
    ('Pan Mollete', 'Harina', '0.050', 'kg'),
    ('Pan Mollete', 'Azúcar', '0.010', 'kg'),
    ('Pan Mollete', 'Leche', '0.010', 'litro'),
    # 11. Pan Galleta
    ('Pan Galleta', 'Harina', '0.040', 'kg'),
    ('Pan Galleta', 'Azúcar', '0.010', 'kg'),
    # 12. Pan de Leche
    ('Pan de Leche', 'Harina', '0.060', 'kg'),
    ('Pan de Leche', 'Leche', '0.030', 'litro'),
    ('Pan de Leche', 'Azúcar', '0.015', 'kg'),
    ('Pan de Leche', 'Mantequilla', '0.010', 'kg'),
]


class Command(BaseCommand):
    help = 'Puebla las recetas oficiales (BOM / MRP) de los 12 panes según Poblacion_4_Dias_Panaderia_Santiago.sql.'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando poblado de recetas de producción (CU10)...')

        productos_map = {p.nombre: p for p in Producto.objects.all()}
        materias_map = {m.nombre: m for m in MateriaPrima.objects.all()}

        if not productos_map:
            self.stdout.write(self.style.ERROR('No hay productos en la base de datos. Ejecute primero seed_productos.'))
            return

        if not materias_map:
            self.stdout.write(self.style.ERROR('No hay materias primas en la base de datos. Ejecute primero seed_materias_primas.'))
            return

        creados = 0
        actualizados = 0

        with transaction.atomic():
            for prod_nom, mat_nom, cant_str, unidad in RECETAS:
                producto = productos_map.get(prod_nom)
                materia = materias_map.get(mat_nom)

                if not producto:
                    self.stdout.write(self.style.WARNING(f'Producto no encontrado: {prod_nom}'))
                    continue
                if not materia:
                    self.stdout.write(self.style.WARNING(f'Materia prima no encontrada: {mat_nom}'))
                    continue

                _, creado = ProductoMateriaPrima.objects.update_or_create(
                    id_producto=producto,
                    id_materia_prima=materia,
                    defaults={
                        'cantidad_requerida': Decimal(cant_str),
                        'unidad_medida': unidad,
                    },
                )
                if creado:
                    creados += 1
                else:
                    actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Recetas pobladas con éxito: {creados} ingredientes registrados, {actualizados} actualizados.'
            )
        )
