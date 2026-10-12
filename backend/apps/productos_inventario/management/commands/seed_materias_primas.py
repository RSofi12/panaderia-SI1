from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.productos_inventario.models import InventarioMateriaPrima, MateriaPrima


class Command(BaseCommand):
    help = 'Carga materias primas de prueba con su inventario (CU8)'

    def handle(self, *args, **options):
        datos = [
            ('Harina de trigo', 'kg', '20', '18.400'),
            ('Avena', 'kg', '5', '5.000'),
            ('Levadura', 'kg', '2', '0'),
            ('Leche', 'L', '10', '21.400'),
        ]
        for nombre, unidad, minimo, actual in datos:
            materia, _ = MateriaPrima.objects.get_or_create(
                nombre=nombre,
                defaults={'unidad_medida': unidad, 'stock_minimo': Decimal(minimo)},
            )
            InventarioMateriaPrima.objects.get_or_create(
                id_materia_prima=materia,
                defaults={'stock_actual': Decimal(actual)},
            )
        self.stdout.write(self.style.SUCCESS('Materias primas de prueba cargadas.'))