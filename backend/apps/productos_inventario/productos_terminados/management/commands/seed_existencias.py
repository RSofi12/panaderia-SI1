"""
Comando de Django para poblar existencias iniciales de prueba (CU12).
Autor: Roberto (Equipo Panadería Santiago).

Uso:
    python manage.py seed_existencias
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    TipoMovimientoProductoTerminado,
)

# Stock inicial realista para los 12 tipos de pan tradicionales de Panadería Santiago
STOCK_INICIAL_MAP = {
    'Marraqueta tradicional': 140,
    'Pan Arani': 80,
    'Pan Chama': 95,
    'Pan Casero': 110,
    'Pan Tortilla': 65,
    'Pan Integral': 30,
    'Pan Gusanito': 45,
    'Pan con Azúcar': 25,
    'Pan Dulce Especial': 15,    # Stock crítico (<20) para probar alertas
    'Pan Mollete': 18,           # Stock crítico (<20)
    'Pan Galleta': 0,            # Stock agotado (0) para probar estado agotado
    'Pan de Leche': 50,
}


class Command(BaseCommand):
    help = 'Puebla el inventario inicial de productos terminados para el CU12 (Existencias de pan en mostrador).'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de existencias de productos terminados (CU12)...')

        productos = Producto.objects.all()
        if not productos.exists():
            self.stdout.write(
                self.style.WARNING(
                    '[AVISO] No se encontraron productos. Ejecuta primero: python manage.py seed_productos'
                )
            )
            return

        with transaction.atomic():
            creados = 0
            actualizados = 0

            for producto in productos:
                # Determinar stock por nombre o valor predeterminado
                stock_deseado = STOCK_INICIAL_MAP.get(producto.nombre, 40)

                inventario, fue_creado = InventarioProductoTerminado.objects.get_or_create(
                    id_producto=producto,
                    defaults={'stock_actual': stock_deseado},
                )

                if fue_creado:
                    creados += 1
                    # Registrar movimiento inicial de apertura de mostrador en Kardex
                    if stock_deseado > 0:
                        MovimientoProductoTerminado.objects.create(
                            id_inventario=inventario,
                            tipo=TipoMovimientoProductoTerminado.ENTRADA,
                            cantidad=stock_deseado,
                            fecha_hora=timezone.now(),
                        )
                else:
                    # Si ya existía, sincronizamos para asegurar que haya stock de prueba si estaba en 0
                    if inventario.stock_actual == 0 and stock_deseado > 0:
                        inventario.stock_actual = stock_deseado
                        inventario.save(update_fields=['stock_actual'])
                        actualizados += 1
                        MovimientoProductoTerminado.objects.create(
                            id_inventario=inventario,
                            tipo=TipoMovimientoProductoTerminado.ENTRADA,
                            cantidad=stock_deseado,
                            fecha_hora=timezone.now(),
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] Existencias procesadas: {creados} inventarios creados, {actualizados} actualizados.'
                )
            )
