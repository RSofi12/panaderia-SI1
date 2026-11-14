"""
Comando para unificar y consolidar las categorías de producto en Panadería Santiago.
Resuelve la sobre-clasificación taxonómica y fusiona productos duplicados (cuñape -> Cuñapé).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.comercializacion.pedidos.models import DetallePedido
from apps.comercializacion.ventas.models import DetalleVenta
from apps.productos_inventario.produccion.models import DetalleProduccion
from apps.productos_inventario.productos.models import (
    CategoriaProducto,
    HistorialPrecioProducto,
    Producto,
    ProductoMateriaPrima,
)
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
)

NUEVAS_CATEGORIAS = [
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

MAPEO_PRODUCTOS = {
    # 1. Panes Tradicionales y de Mesa
    'Marraqueta': 'Panes Tradicionales y de Mesa',
    'Casero': 'Panes Tradicionales y de Mesa',
    'Tortilla': 'Panes Tradicionales y de Mesa',
    'Pan de Molde Casero': 'Panes Tradicionales y de Mesa',
    'Pan de Leche': 'Panes Tradicionales y de Mesa',
    'Pan Mollete': 'Panes Tradicionales y de Mesa',
    'Pan Galleta': 'Panes Tradicionales y de Mesa',

    # 2. Masas Típicas y Regionales
    'Cuñapé': 'Masas Típicas y Regionales',
    'Sonso de Yuca': 'Masas Típicas y Regionales',
    'Masaco de Yuca': 'Masas Típicas y Regionales',
    'Arani': 'Masas Típicas y Regionales',
    'Chama': 'Masas Típicas y Regionales',

    # 3. Repostería y Panes Dulces
    'Pan Dulce': 'Repostería y Panes Dulces',
    'Pan con Azúcar': 'Repostería y Panes Dulces',
    'Gusanito': 'Repostería y Panes Dulces',
    'Rollo de Canela': 'Repostería y Panes Dulces',
    'Pastel de Choclo': 'Repostería y Panes Dulces',
    'Queque de Zanahoria': 'Repostería y Panes Dulces',
    'Queque de Banana': 'Repostería y Panes Dulces',
    'Panetón con Chocolate': 'Repostería y Panes Dulces',
    'Trenza Suiza': 'Repostería y Panes Dulces',

    # 4. Salados y Especialidades
    'Salteña Tradicional': 'Salados y Especialidades',
    'Tamal a la Olla': 'Salados y Especialidades',
    'Empanada Integral': 'Salados y Especialidades',
    'Empanada Frita de Queso': 'Salados y Especialidades',
    'Pan Pizza': 'Salados y Especialidades',

    # 5. Panadería Rústica y Gourmet
    'Integral': 'Panadería Rústica y Gourmet',
    'Dobladillo Integral': 'Panadería Rústica y Gourmet',
    'Pan con Queso Integral': 'Panadería Rústica y Gourmet',
    'Pan de Centeno': 'Panadería Rústica y Gourmet',
    'Croissant': 'Panadería Rústica y Gourmet',
    'Pan Brioche': 'Panadería Rústica y Gourmet',
    'Pan Baguette': 'Panadería Rústica y Gourmet',
    'Bagel Tradicional': 'Panadería Rústica y Gourmet',
    'Pan Ciabatta': 'Panadería Rústica y Gourmet',
    'Focaccia Artesanal': 'Panadería Rústica y Gourmet',
}


class Command(BaseCommand):
    help = 'Consolida las categorías en 5 grupos maestros y fusiona duplicados de productos.'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando consolidación de categorías y deduplicación...')

        with transaction.atomic():
            # 1. Crear / Asegurar las 5 categorías maestras
            categorias_maestras = {}
            for nombre, desc in NUEVAS_CATEGORIAS:
                cat, _ = CategoriaProducto.objects.update_or_create(
                    nombre=nombre,
                    defaults={
                        'descripcion': desc,
                        'activo': True,
                        'estado': 'Activo',
                    },
                )
                categorias_maestras[nombre] = cat

            # 2. Fusionar producto duplicado cuñape -> Cuñapé
            p_src = Producto.objects.filter(nombre='cuñape').first()
            p_tgt = Producto.objects.filter(nombre='Cuñapé').first()

            if p_src and p_tgt and p_src.id_producto != p_tgt.id_producto:
                self.stdout.write(f'Fusionando producto id {p_src.id_producto} ({p_src.nombre}) en id {p_tgt.id_producto} ({p_tgt.nombre})...')

                # Reasignar ventas
                n_ventas = DetalleVenta.objects.filter(id_producto=p_src).update(id_producto=p_tgt)
                # Reasignar producción
                n_prod = DetalleProduccion.objects.filter(id_producto=p_src).update(id_producto=p_tgt)
                # Reasignar pedidos
                n_ped = DetallePedido.objects.filter(id_producto=p_src).update(id_producto=p_tgt)
                # Reasignar precios
                HistorialPrecioProducto.objects.filter(id_producto=p_src).update(id_producto=p_tgt)

                # Reasignar inventario
                inv_src = InventarioProductoTerminado.objects.filter(id_producto=p_src).first()
                inv_tgt = InventarioProductoTerminado.objects.filter(id_producto=p_tgt).first()

                if inv_src and inv_tgt:
                    inv_tgt.stock_actual += inv_src.stock_actual
                    inv_tgt.save()
                    MovimientoProductoTerminado.objects.filter(id_inventario=inv_src).update(id_inventario=inv_tgt)
                    inv_src.delete()
                elif inv_src and not inv_tgt:
                    inv_src.id_producto = p_tgt
                    inv_src.save()

                # Reasignar o eliminar recetas duplicadas
                for ing_src in ProductoMateriaPrima.objects.filter(id_producto=p_src):
                    existe_en_tgt = ProductoMateriaPrima.objects.filter(
                        id_producto=p_tgt,
                        id_materia_prima=ing_src.id_materia_prima,
                    ).exists()
                    if existe_en_tgt:
                        ing_src.delete()
                    else:
                        ing_src.id_producto = p_tgt
                        ing_src.save()

                p_src.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'Fusión completada: {n_ventas} ventas y {n_prod} lotes de producción transferidos a "Cuñapé".'
                ))

            # 3. Reclasificar los productos a las 5 categorías
            reasignados = 0
            for nombre_prod, nombre_cat in MAPEO_PRODUCTOS.items():
                cat_destino = categorias_maestras[nombre_cat]
                prods = Producto.objects.filter(nombre=nombre_prod)
                for p in prods:
                    if p.id_categoria != cat_destino:
                        p.id_categoria = cat_destino
                        p.save(update_fields=['id_categoria'])
                        reasignados += 1

            self.stdout.write(f'{reasignados} productos reasignados a las 5 categorías maestras.')

            # 4. Inactivar o remover categorías obsoletas que ya no tienen productos
            nombres_maestros = set(categorias_maestras.keys())
            cats_antiguas = CategoriaProducto.objects.exclude(nombre__in=nombres_maestros)
            for c in cats_antiguas:
                cant_prods = c.productos.count()
                if cant_prods == 0:
                    c.delete()
                else:
                    c.activo = False
                    c.estado = 'Inactivo'
                    c.save(update_fields=['activo', 'estado'])

        self.stdout.write(self.style.SUCCESS('Consolidación completada exitosamente.'))
