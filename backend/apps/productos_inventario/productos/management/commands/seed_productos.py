from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.productos.models import CategoriaProducto, HistorialPrecioProducto, Producto

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql
CATEGORIAS = [
    (
        'Panes Tradicionales y de Mesa',
        'Panes clásicos de consumo diario y desayuno popular (marraqueta, casero, molde, tortilla, leche, mollete, galleta)',
    ),
    (
        'Masas Típicas y Regionales',
        'Horneados tradicionales del patrimonio cruceño y boliviano (cuñapé, sonso, masaco, arani, chama)',
    ),
    (
        'Repostería y Panes Dulces',
        'Masas dulces, queques y pastelería tradicional (rollo de canela, queques, pastel de choclo, panetón, gusanito, panes dulces)',
    ),
    (
        'Salados y Especialidades',
        'Opciones saladas calientes, salteñería y empanadas (salteña, tamal, empanadas, pan pizza)',
    ),
    (
        'Panadería Rústica y Gourmet',
        'Panes de masa madre, integrales, centeno y especialidades europeas (integral, centeno, croissant, brioche, baguette, bagel, ciabatta, focaccia)',
    ),
]

# (categoría, nombre, descripción, costo_produccion, porcentaje_ganancia, precio_venta)
PRODUCTOS = [
    # 1. Panes Tradicionales y de Mesa
    ('Panes Tradicionales y de Mesa', 'Marraqueta', 'Pan tradicional cruceño de corteza crujiente', '0.40', '50.00', '0.60'),
    ('Panes Tradicionales y de Mesa', 'Casero', 'Pan casero de miga suave', '0.45', '55.00', '0.70'),
    ('Panes Tradicionales y de Mesa', 'Tortilla', 'Pan tipo tortilla de mayor tamaño', '1.20', '45.00', '1.75'),
    ('Panes Tradicionales y de Mesa', 'Pan de Molde Casero', 'Hogaza de pan blanco de molde rebanado para tostadas', '5.50', '100.00', '11.00'),
    ('Panes Tradicionales y de Mesa', 'Pan de Leche', 'Pan suave con alto contenido de leche', '0.80', '55.00', '1.25'),
    ('Panes Tradicionales y de Mesa', 'Pan Mollete', 'Panecillo pequeño suave', '0.40', '50.00', '0.60'),
    ('Panes Tradicionales y de Mesa', 'Pan Galleta', 'Panecillo pequeño crocante', '0.35', '45.00', '0.50'),

    # 2. Masas Típicas y Regionales
    ('Masas Típicas y Regionales', 'Cuñapé', 'Horneado tradicional cruceño a base de almidón y queso criollo', '2.00', '75.00', '3.50'),
    ('Masas Típicas y Regionales', 'Sonso de Yuca', 'Masa horneada de yuca fresca con abundante queso', '2.80', '78.57', '5.00'),
    ('Masas Típicas y Regionales', 'Masaco de Yuca', 'Yuca frita machacada con charque cruceño crocante', '3.50', '71.43', '6.00'),
    ('Masas Típicas y Regionales', 'Arani', 'Pan regional de sabor característico', '0.50', '60.00', '0.80'),
    ('Masas Típicas y Regionales', 'Chama', 'Pan regional dulce suave', '0.55', '60.00', '0.90'),

    # 3. Repostería y Panes Dulces
    ('Repostería y Panes Dulces', 'Pan Dulce', 'Pan con azúcar, huevo y mantequilla', '0.70', '55.00', '1.10'),
    ('Repostería y Panes Dulces', 'Pan con Azúcar', 'Pan espolvoreado con azúcar', '0.65', '55.00', '1.00'),
    ('Repostería y Panes Dulces', 'Gusanito', 'Pan relleno tipo gusanito', '1.00', '50.00', '1.50'),
    ('Repostería y Panes Dulces', 'Rollo de Canela', 'Espiral dulce con mantequilla, canela molida y glaseado suave', '2.50', '100.00', '5.00'),
    ('Repostería y Panes Dulces', 'Pastel de Choclo', 'Porción de pastel horneado de choclo dulce y queso', '3.50', '100.00', '7.00'),
    ('Repostería y Panes Dulces', 'Queque de Zanahoria', 'Porción de queque esponjoso con zanahoria fresca y canela', '3.00', '100.00', '6.00'),
    ('Repostería y Panes Dulces', 'Queque de Banana', 'Porción de queque artesanal con plátano maduro', '2.80', '96.43', '5.50'),
    ('Repostería y Panes Dulces', 'Panetón con Chocolate', 'Panetón navideño especial con chispas de chocolate fino', '18.00', '94.44', '35.00'),
    ('Repostería y Panes Dulces', 'Trenza Suiza', 'Pan dulce trenzado con mantequilla y glaseado', '3.50', '100.00', '7.00'),

    # 4. Salados y Especialidades
    ('Salados y Especialidades', 'Salteña Tradicional', 'Empanada jugosa rellena de pollo, papa y arvejas', '4.00', '100.00', '8.00'),
    ('Salados y Especialidades', 'Tamal a la Olla', 'Masa suave de choclo tierno con carne y queso cocida a la olla', '3.50', '100.00', '7.00'),
    ('Salados y Especialidades', 'Empanada Integral', 'Empanada horneada de masa integral con queso y verduras', '3.00', '100.00', '6.00'),
    ('Salados y Especialidades', 'Empanada Frita de Queso', 'Empanada crocante rellena de queso criollo', '2.50', '100.00', '5.00'),
    ('Salados y Especialidades', 'Pan Pizza', 'Base crocante de pan con salsa de tomate, queso y orégano', '2.80', '96.43', '5.50'),

    # 5. Panadería Rústica y Gourmet
    ('Panadería Rústica y Gourmet', 'Integral', 'Pan elaborado con harina integral', '0.60', '50.00', '0.90'),
    ('Panadería Rústica y Gourmet', 'Dobladillo Integral', 'Pan integral en capas finas de masa crujiente', '0.80', '87.50', '1.50'),
    ('Panadería Rústica y Gourmet', 'Pan con Queso Integral', 'Pan integral relleno con queso criollo al centro', '1.20', '108.33', '2.50'),
    ('Panadería Rústica y Gourmet', 'Pan de Centeno', 'Pan rústico de masa madre y harina de centeno aromático', '1.50', '100.00', '3.00'),
    ('Panadería Rústica y Gourmet', 'Croissant', 'Masa hojaldrada francesa con pura mantequilla artesanal', '2.20', '104.55', '4.50'),
    ('Panadería Rústica y Gourmet', 'Pan Brioche', 'Pan francés suave y esponjoso enriquecido con huevo y mantequilla', '2.00', '100.00', '4.00'),
    ('Panadería Rústica y Gourmet', 'Pan Baguette', 'Barra clásica de pan francés de corteza muy crujiente', '1.80', '94.44', '3.50'),
    ('Panadería Rústica y Gourmet', 'Bagel Tradicional', 'Pan redondo con agujero hervido y horneado estilo neoyorquino', '1.20', '108.33', '2.50'),
    ('Panadería Rústica y Gourmet', 'Pan Ciabatta', 'Pan italiano de alta hidratación y alvéolos grandes', '1.20', '108.33', '2.50'),
    ('Panadería Rústica y Gourmet', 'Focaccia Artesanal', 'Pan plano italiano horneado con aceite de oliva y hierbas', '2.50', '100.00', '5.00'),
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
                    defaults={
                        'descripcion': descripcion,
                        'activo': True,
                        'estado': 'Activo',
                    },
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
                        'activo': True,
                    },
                )
                if not creado:
                    if producto.id_categoria != categorias[categoria]:
                        producto.id_categoria = categorias[categoria]
                        producto.save(update_fields=['id_categoria'])
                    continue

                creados += 1
                HistorialPrecioProducto.objects.create(
                    id_producto=producto,
                    precio=Decimal(precio),
                    fecha_inicio=fecha_inicial,
                )

            # Limpiar categorías obsoletas que ya no tienen productos
            nombres_maestros = set(categorias.keys())
            for c in CategoriaProducto.objects.exclude(nombre__in=nombres_maestros):
                if c.productos.count() == 0:
                    c.delete()

        self.stdout.write(self.style.SUCCESS(
            f'{creados} productos nuevos creados; {len(PRODUCTOS) - creados} ya existian.'
        ))
