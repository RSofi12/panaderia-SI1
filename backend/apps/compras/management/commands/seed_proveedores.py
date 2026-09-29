from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.compras.models import Proveedor

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql
PROVEEDORES = [
    ('Molinos del Oriente S.R.L.', '33210099', 'Parque Industrial, Santa Cruz'),
    ('Distribuidora Lácteos Santa Cruz', '33220188', 'Av. Grigotá, 6to anillo'),
    ('Insumos y Levaduras Bolivia', '33230277', 'Av. Piraí, 4to anillo'),
]


class Command(BaseCommand):
    help = 'Puebla el maestro de proveedores de la Panadería Santiago (CU6).'

    def handle(self, *args, **options):
        fecha_inicial = timezone.make_aware(datetime(2026, 7, 15, 10, 0))
        creados = 0

        with transaction.atomic():
            for nombre, telefono, direccion in PROVEEDORES:
                _, creado = Proveedor.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'telefono': telefono,
                        'direccion': direccion,
                        'fecha_registro': fecha_inicial,
                        'activo': True,
                    },
                )
                if creado:
                    creados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{creados} proveedores nuevos; {len(PROVEEDORES) - creados} ya existian y no se modificaron.'
        ))
