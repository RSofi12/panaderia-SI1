from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.models import CategoriaProducto, HistorialPrecioProducto, Producto

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql
CATEGORIAS = [
    ('Panes Tradicionales', 'Panes clásicos de consumo diario (marraqueta, casero, tortilla)'),
    ('Panes Regionales', 'Variedades típicas de la región cruceña (arani, chama)'),
    ('Panes Integrales', 'Panes elaborados con harina integral'),
    ('Panes Dulces', 'Panes con un toque dulce o azucarado'),
    ('Panes Rellenos', 'Panes con relleno, como el gusanito'),
    ('Panecillos Pequeños', 'Panes de tamaño reducido (mollete, galleta)'),
    ('Panes de Leche', 'Panes elaborados con mayor proporción de leche'),
]

# (categoría, nombre, descripción, costo_produccion, porcentaje_ganancia, precio_venta)
PRODUCTOS = [
    ('Panes Tradicionales', 'Marraqueta', 'Pan tradicional cruceño de corteza crujiente', '0.40', '50.00', '0.60'),
    ('Panes Tradicionales', 'Casero', 'Pan casero de miga suave', '0.45', '55.00', '0.70'),
    ('Panes Tradicionales', 'Tortilla', 'Pan tipo tortilla de mayor tamaño', '1.20', '45.00', '1.75'),
    ('Panes Regionales', 'Arani', 'Pan regional de sabor característico', '0.50', '60.00', '0.80'),
    ('Panes Regionales', 'Chama', 'Pan regional dulce suave', '0.55', '60.00', '0.90'),
    ('Panes Integrales', 'Integral', 'Pan elaborado con harina integral', '0.60', '50.00', '0.90'),
    ('Panes Dulces', 'Pan Dulce', 'Pan con azúcar, huevo y mantequilla', '0.70', '55.00', '1.10'),
    ('Panes Dulces', 'Pan con Azúcar', 'Pan espolvoreado con azúcar', '0.65', '55.00', '1.00'),
    ('Panes Rellenos', 'Gusanito', 'Pan relleno tipo gusanito', '1.00', '50.00', '1.50'),
    ('Panecillos Pequeños', 'Pan Mollete', 'Panecillo pequeño suave', '0.40', '50.00', '0.60'),
    ('Panecillos Pequeños', 'Pan Galleta', 'Panecillo pequeño crocante', '0.35', '45.00', '0.50'),
    ('Panes de Leche', 'Pan de Leche', 'Pan suave con alto contenido de leche', '0.80', '55.00', '1.25'),
]


class Command(BaseCommand):
    help = 'Puebla el catálogo base de categorías y productos de la Panadería Santiago (CU5).'

    def handle(self, *args, **options):
        fecha_inicial = timezone.make_aware(datetime(2026, 8, 1, 8, 0))

        with transaction.atomic():
            categorias = {}
            for nombre, descripcion in CATEGORIAS:
                categoria, _ = CategoriaProducto.objects.update_or_create(
                    nombre=nombre,
                    defaults={'descripcion': descripcion},
                )
                categorias[nombre] = categoria

            creados = 0
            for categoria, nombre, descripcion, costo, ganancia, precio in PRODUCTOS:
                producto, creado = Producto.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'id_categoria': categorias[categoria],
                        'descripcion': descripcion,
                        'costo_produccion': Decimal(costo),
                        'porcentaje_ganancia': Decimal(ganancia),
                        'precio_venta': Decimal(precio),
                        'fecha_registro': fecha_inicial,
                    },
                )
                if creado:
                    creados += 1
                    HistorialPrecioProducto.objects.create(
                        id_producto=producto,
                        precio=producto.precio_venta,
                        fecha_inicio=fecha_inicial,
                    )

        self.stdout.write(self.style.SUCCESS(f'{len(categorias)} categorias procesadas.'))
        self.stdout.write(self.style.SUCCESS(
            f'{creados} productos nuevos; {len(PRODUCTOS) - creados} ya existian y no se modificaron.'
        ))
