from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
)

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql (módulo inventario MP)
# (nombre, unidad_medida, stock_minimo, precio_inicial_bs)
INSUMOS = [
    ('Harina', 'kg', '20.000', '4.50'),
    ('Azúcar', 'kg', '10.000', '6.00'),
    ('Levadura', 'kg', '2.000', '45.00'),
    ('Sal', 'kg', '3.000', '3.00'),
    ('Huevos', 'unidad', '100.000', '0.90'),
    ('Leche', 'litro', '15.000', '7.50'),
    ('Mantequilla', 'kg', '5.000', '35.00'),
    ('Queso Criollo', 'kg', '10.000', '32.00'),
    ('Almidón de Yuca', 'kg', '15.000', '18.00'),
    ('Yuca Fresca', 'kg', '20.000', '5.00'),
    ('Choclo Desgranado', 'kg', '10.000', '12.00'),
    ('Harina de Centeno', 'kg', '10.000', '9.50'),
    ('Harina Integral', 'kg', '15.000', '7.00'),
    ('Carne de Pollo Relleno', 'kg', '8.000', '24.00'),
    ('Charque Vacuno', 'kg', '5.000', '65.00'),
    ('Chocolate Cobertura', 'kg', '5.000', '48.00'),
    ('Canela en Polvo', 'kg', '1.000', '80.00'),
    ('Zanahoria Rallada', 'kg', '5.000', '6.00'),
    ('Plátano y Banana', 'kg', '8.000', '7.00'),
    ('Aceitunas Negras', 'kg', '2.000', '35.00'),
]


class Command(BaseCommand):
    help = (
        'Puebla materias primas, inventario en 0 y precio inicial de compra '
        '(catálogo CU7 / inventario).'
    )

    def handle(self, *args, **options):
        fecha_inicial = timezone.make_aware(datetime(2026, 8, 1, 8, 0))

        with transaction.atomic():
            creados = 0
            for nombre, unidad, stock_minimo, precio in INSUMOS:
                materia, creado = MateriaPrima.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'unidad_medida': unidad,
                        'stock_minimo': Decimal(stock_minimo),
                        'fecha_registro': fecha_inicial,
                        'activo': True,
                    },
                )
                if not creado:
                    continue

                creados += 1
                InventarioMateriaPrima.objects.create(
                    id_materia_prima=materia,
                    stock_actual=Decimal('0'),
                )
                HistorialPrecioMateriaPrima.objects.create(
                    id_materia_prima=materia,
                    precio=Decimal(precio),
                    fecha_inicio=fecha_inicial,
                )

        self.stdout.write(self.style.SUCCESS(
            f'{creados} materias primas creadas con inventario inicial e historial de precio.'
        ))
