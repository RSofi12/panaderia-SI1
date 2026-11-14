from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.productos.models import CategoriaProducto, HistorialPrecioProducto, Producto

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql
CATEGORIAS = [
    ('Panes Tradicionales', 'Panes clásicos de consumo diario (marraqueta, casero, tortilla)'),
    ('Panes Regionales', 'Variedades típicas de la región cruceña (arani, chama)'),
    ('Panes Integrales', 'Panes elaborados con harina integral y de centeno'),
    ('Panes Dulces', 'Panes con un toque dulce o azucarado'),
    ('Panes Rellenos', 'Panes con relleno, como el gusanito'),
    ('Panecillos Pequeños', 'Panes de tamaño reducido (mollete, galleta)'),
    ('Panes de Leche', 'Panes elaborados con mayor proporción de leche'),
    ('Masas Típicas Cruceñas', 'Horneados tradicionales del oriente boliviano (cuñapé, sonso, masaco)'),
    ('Repostería y Queques', 'Queques, pasteles de choclo y panes dulces festivos'),
    ('Salados y Especialidades', 'Salteñas, tamales, empanadas y especialidades calientes'),
    ('Panadería Gourmet y Rústica', 'Panes europeos, baguette, croissants y fermentación lenta'),
]

# (categoría, nombre, descripción, costo_produccion, porcentaje_ganancia, precio_venta)
PRODUCTOS = [
    ('Panes Tradicionales', 'Marraqueta', 'Pan tradicional cruceño de corteza crujiente', '0.40', '50.00', '0.60'),
    ('Panes Tradicionales', 'Casero', 'Pan casero de miga suave', '0.45', '55.00', '0.70'),
    ('Panes Tradicionales', 'Tortilla', 'Pan tipo tortilla de mayor tamaño', '1.20', '45.00', '1.75'),
    ('Panes Tradicionales', 'Pan de Molde Casero', 'Hogaza de pan blanco de molde rebanado para tostadas', '5.50', '100.00', '11.00'),
    ('Panes Regionales', 'Arani', 'Pan regional de sabor característico', '0.50', '60.00', '0.80'),
    ('Panes Regionales', 'Chama', 'Pan regional dulce suave', '0.55', '60.00', '0.90'),
    ('Panes Integrales', 'Integral', 'Pan elaborado con harina integral', '0.60', '50.00', '0.90'),
    ('Panes Integrales', 'Dobladillo Integral', 'Pan integral en capas finas de masa crujiente', '0.80', '87.50', '1.50'),
    ('Panes Integrales', 'Pan con Queso Integral', 'Pan integral relleno con queso criollo al centro', '1.20', '108.33', '2.50'),
    ('Panes Integrales', 'Pan de Centeno', 'Pan rústico de masa madre y harina de centeno aromático', '1.50', '100.00', '3.00'),
    ('Panes Dulces', 'Pan Dulce', 'Pan con azúcar, huevo y mantequilla', '0.70', '55.00', '1.10'),
    ('Panes Dulces', 'Pan con Azúcar', 'Pan espolvoreado con azúcar', '0.65', '55.00', '1.00'),
    ('Panes Rellenos', 'Gusanito', 'Pan relleno tipo gusanito', '1.00', '50.00', '1.50'),
    ('Panecillos Pequeños', 'Pan Mollete', 'Panecillo pequeño suave', '0.40', '50.00', '0.60'),
    ('Panecillos Pequeños', 'Pan Galleta', 'Panecillo pequeño crocante', '0.35', '45.00', '0.50'),
    ('Panes de Leche', 'Pan de Leche', 'Pan suave con alto contenido de leche', '0.80', '55.00', '1.25'),
    ('Masas Típicas Cruceñas', 'Cuñapé', 'Horneado tradicional cruceño a base de almidón y queso criollo', '2.00', '75.00', '3.50'),
    ('Masas Típicas Cruceñas', 'Sonso de Yuca', 'Masa horneada de yuca fresca con abundante queso', '2.80', '78.57', '5.00'),
    ('Masas Típicas Cruceñas', 'Masaco de Yuca', 'Yuca frita machacada con charque cruceño crocante', '3.50', '71.43', '6.00'),
    ('Salados y Especialidades', 'Salteña Tradicional', 'Empanada jugosa rellena de pollo, papa y arvejas', '4.00', '100.00', '8.00'),
    ('Salados y Especialidades', 'Tamal a la Olla', 'Masa suave de choclo tierno con carne y queso cocida a la olla', '3.50', '100.00', '7.00'),
    ('Salados y Especialidades', 'Empanada Integral', 'Empanada horneada de masa integral con queso y verduras', '3.00', '100.00', '6.00'),
    ('Salados y Especialidades', 'Empanada Frita de Queso', 'Empanada crocante rellena de queso criollo', '2.50', '100.00', '5.00'),
    ('Salados y Especialidades', 'Pan Pizza', 'Base crocante de pan con salsa de tomate, queso y orégano', '2.80', '96.43', '5.50'),
    ('Repostería y Queques', 'Rollo de Canela', 'Espiral dulce con mantequilla, canela molida y glaseado suave', '2.50', '100.00', '5.00'),
    ('Repostería y Queques', 'Pastel de Choclo', 'Porción de pastel horneado de choclo dulce y queso', '3.50', '100.00', '7.00'),
    ('Repostería y Queques', 'Queque de Zanahoria', 'Porción de queque esponjoso con zanahoria fresca y canela', '3.00', '100.00', '6.00'),
    ('Repostería y Queques', 'Queque de Banana', 'Porción de queque artesanal con plátano maduro', '2.80', '96.43', '5.50'),
    ('Repostería y Queques', 'Panetón con Chocolate', 'Panetón navideño especial con chispas de chocolate fino', '18.00', '94.44', '35.00'),
    ('Repostería y Queques', 'Trenza Suiza', 'Pan dulce trenzado con mantequilla y glaseado', '3.50', '100.00', '7.00'),
    ('Panadería Gourmet y Rústica', 'Croissant', 'Masa hojaldrada francesa con pura mantequilla artesanal', '2.20', '104.55', '4.50'),
    ('Panadería Gourmet y Rústica', 'Pan Brioche', 'Pan francés suave y esponjoso enriquecido con huevo y mantequilla', '2.00', '100.00', '4.00'),
    ('Panadería Gourmet y Rústica', 'Pan Baguette', 'Barra clásica de pan francés de corteza muy crujiente', '1.80', '94.44', '3.50'),
    ('Panadería Gourmet y Rústica', 'Bagel Tradicional', 'Pan redondo con agujero hervido y horneado estilo neoyorquino', '1.20', '108.33', '2.50'),
    ('Panadería Gourmet y Rústica', 'Pan Ciabatta', 'Pan italiano de alta hidratación y alvéolos grandes', '1.20', '108.33', '2.50'),
    ('Panadería Gourmet y Rústica', 'Focaccia Artesanal', 'Pan plano italiano horneado con aceite de oliva y hierbas', '2.50', '100.00', '5.00'),
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
                    continue

                creados += 1
                HistorialPrecioProducto.objects.create(
                    id_producto=producto,
                    precio=Decimal(precio),
                    fecha_inicio=fecha_inicial,
                )

        self.stdout.write(self.style.SUCCESS(
            f'{creados} productos nuevos creados; {len(PRODUCTOS) - creados} ya existian.'
        ))
