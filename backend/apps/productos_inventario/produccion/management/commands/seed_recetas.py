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
    # 13. Cuñapé
    ('Cuñapé', 'Almidón de Yuca', '0.040', 'kg'),
    ('Cuñapé', 'Queso Criollo', '0.050', 'kg'),
    ('Cuñapé', 'Huevos', '0.030', 'unidad'),
    ('Cuñapé', 'Leche', '0.015', 'litro'),
    # 14. Sonso de Yuca
    ('Sonso de Yuca', 'Yuca Fresca', '0.120', 'kg'),
    ('Sonso de Yuca', 'Queso Criollo', '0.060', 'kg'),
    ('Sonso de Yuca', 'Mantequilla', '0.010', 'kg'),
    # 15. Masaco de Yuca
    ('Masaco de Yuca', 'Yuca Fresca', '0.140', 'kg'),
    ('Masaco de Yuca', 'Charque Vacuno', '0.040', 'kg'),
    # 16. Salteña Tradicional
    ('Salteña Tradicional', 'Harina', '0.060', 'kg'),
    ('Salteña Tradicional', 'Carne de Pollo Relleno', '0.050', 'kg'),
    ('Salteña Tradicional', 'Huevos', '0.020', 'unidad'),
    ('Salteña Tradicional', 'Aceitunas Negras', '0.010', 'kg'),
    # 17. Tamal a la Olla
    ('Tamal a la Olla', 'Choclo Desgranado', '0.150', 'kg'),
    ('Tamal a la Olla', 'Carne de Pollo Relleno', '0.040', 'kg'),
    ('Tamal a la Olla', 'Queso Criollo', '0.030', 'kg'),
    # 18. Empanada Integral
    ('Empanada Integral', 'Harina Integral', '0.060', 'kg'),
    ('Empanada Integral', 'Queso Criollo', '0.030', 'kg'),
    # 19. Empanada Frita de Queso
    ('Empanada Frita de Queso', 'Harina', '0.060', 'kg'),
    ('Empanada Frita de Queso', 'Queso Criollo', '0.040', 'kg'),
    # 20. Pan Pizza
    ('Pan Pizza', 'Harina', '0.080', 'kg'),
    ('Pan Pizza', 'Queso Criollo', '0.040', 'kg'),
    # 21. Rollo de Canela
    ('Rollo de Canela', 'Harina', '0.070', 'kg'),
    ('Rollo de Canela', 'Canela en Polvo', '0.005', 'kg'),
    ('Rollo de Canela', 'Azúcar', '0.025', 'kg'),
    ('Rollo de Canela', 'Mantequilla', '0.015', 'kg'),
    # 22. Pastel de Choclo
    ('Pastel de Choclo', 'Choclo Desgranado', '0.120', 'kg'),
    ('Pastel de Choclo', 'Queso Criollo', '0.040', 'kg'),
    ('Pastel de Choclo', 'Azúcar', '0.020', 'kg'),
    # 23. Queque de Zanahoria
    ('Queque de Zanahoria', 'Harina', '0.050', 'kg'),
    ('Queque de Zanahoria', 'Zanahoria Rallada', '0.040', 'kg'),
    ('Queque de Zanahoria', 'Azúcar', '0.025', 'kg'),
    ('Queque de Zanahoria', 'Huevos', '0.040', 'unidad'),
    # 24. Queque de Banana
    ('Queque de Banana', 'Harina', '0.050', 'kg'),
    ('Queque de Banana', 'Plátano y Banana', '0.050', 'kg'),
    ('Queque de Banana', 'Azúcar', '0.025', 'kg'),
    # 25. Panetón con Chocolate
    ('Panetón con Chocolate', 'Harina', '0.350', 'kg'),
    ('Panetón con Chocolate', 'Chocolate Cobertura', '0.120', 'kg'),
    ('Panetón con Chocolate', 'Mantequilla', '0.060', 'kg'),
    ('Panetón con Chocolate', 'Huevos', '0.150', 'unidad'),
    # 26. Trenza Suiza
    ('Trenza Suiza', 'Harina', '0.120', 'kg'),
    ('Trenza Suiza', 'Mantequilla', '0.030', 'kg'),
    ('Trenza Suiza', 'Leche', '0.040', 'litro'),
    # 27. Dobladillo Integral
    ('Dobladillo Integral', 'Harina Integral', '0.070', 'kg'),
    ('Dobladillo Integral', 'Mantequilla', '0.010', 'kg'),
    # 28. Pan con Queso Integral
    ('Pan con Queso Integral', 'Harina Integral', '0.070', 'kg'),
    ('Pan con Queso Integral', 'Queso Criollo', '0.025', 'kg'),
    # 29. Pan de Centeno
    ('Pan de Centeno', 'Harina de Centeno', '0.090', 'kg'),
    ('Pan de Centeno', 'Levadura', '0.003', 'kg'),
    ('Pan de Centeno', 'Sal', '0.002', 'kg'),
    # 30. Pan de Molde Casero
    ('Pan de Molde Casero', 'Harina', '0.400', 'kg'),
    ('Pan de Molde Casero', 'Mantequilla', '0.040', 'kg'),
    ('Pan de Molde Casero', 'Leche', '0.100', 'litro'),
    # 31. Croissant
    ('Croissant', 'Harina', '0.060', 'kg'),
    ('Croissant', 'Mantequilla', '0.030', 'kg'),
    ('Croissant', 'Leche', '0.020', 'litro'),
    # 32. Pan Brioche
    ('Pan Brioche', 'Harina', '0.070', 'kg'),
    ('Pan Brioche', 'Mantequilla', '0.025', 'kg'),
    ('Pan Brioche', 'Huevos', '0.050', 'unidad'),
    # 33. Pan Baguette
    ('Pan Baguette', 'Harina', '0.160', 'kg'),
    ('Pan Baguette', 'Levadura', '0.003', 'kg'),
    ('Pan Baguette', 'Sal', '0.003', 'kg'),
    # 34. Bagel Tradicional
    ('Bagel Tradicional', 'Harina', '0.080', 'kg'),
    ('Bagel Tradicional', 'Levadura', '0.002', 'kg'),
    ('Bagel Tradicional', 'Azúcar', '0.010', 'kg'),
    # 35. Pan Ciabatta
    ('Pan Ciabatta', 'Harina', '0.090', 'kg'),
    ('Pan Ciabatta', 'Levadura', '0.002', 'kg'),
    ('Pan Ciabatta', 'Sal', '0.002', 'kg'),
    # 36. Focaccia Artesanal
    ('Focaccia Artesanal', 'Harina', '0.140', 'kg'),
    ('Focaccia Artesanal', 'Sal', '0.003', 'kg'),
    ('Focaccia Artesanal', 'Levadura', '0.003', 'kg'),
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
