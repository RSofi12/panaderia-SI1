from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.compras.proveedores.models import Proveedor

# Fuente: docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql
PROVEEDORES = [
    ('Molinos del Oriente S.R.L.', '33210099', 'Parque Industrial, Santa Cruz'),
    ('Distribuidora Lácteos Santa Cruz', '33220188', 'Av. Grigotá, 6to anillo'),
    ('Insumos y Levaduras Bolivia', '33230277', 'Av. Piraí, 4to anillo'),
    ('Avícola Sofía S.A.', '33520011', 'Av. Cristo Redentor, Km 8 1/2'),
    ('Ingenio Azucarero Guabirá S.A.', '39220050', 'Carretera al Norte Km 52, Montero'),
    ('Distribuidora San Juan (Almidones y Tubérculos)', '33640022', 'Mercado Abasto Mayorista, Galpón 4'),
    ('Lácteos y Quesos Chaqueños', '33480033', 'Av. Tres Pasos al Frente, 3er anillo'),
    ('Chocolates y Especias Para Ti / Repostería', '33350044', 'Calle 24 de Septiembre #145'),
    ('Molino Harinero San Gabriel', '33710055', 'Parque Industrial Mza. 22'),
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
