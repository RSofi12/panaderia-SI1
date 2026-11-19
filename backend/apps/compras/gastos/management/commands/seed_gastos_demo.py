"""
Comando de poblado de Gastos e Inversiones (CU20).
Puebla los movimientos económicos según Poblacion_4_Dias_Panaderia_Santiago.sql.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.compras.gastos.models import MovimientoEconomico, TipoMovimientoEconomico

Usuario = get_user_model()

GASTOS_DATA = [
    (
        TipoMovimientoEconomico.GASTO,
        'Alquiler del local',
        'Pago mensual de alquiler del establecimiento',
        Decimal('1500.00'),
        datetime(2026, 9, 6, 8, 0),
    ),
    (
        TipoMovimientoEconomico.INVERSION,
        'Compra de horno industrial',
        'Nuevo horno para incrementar capacidad de producción',
        Decimal('8000.00'),
        datetime(2026, 9, 6, 9, 0),
    ),
    (
        TipoMovimientoEconomico.GASTO,
        'Energía eléctrica',
        'Pago de factura de luz del mes',
        Decimal('350.00'),
        datetime(2026, 9, 7, 8, 0),
    ),
    (
        TipoMovimientoEconomico.GASTO,
        'Agua potable',
        'Pago de factura de agua del mes',
        Decimal('120.00'),
        datetime(2026, 9, 7, 8, 15),
    ),
    (
        TipoMovimientoEconomico.GASTO,
        'Mantenimiento de horno',
        'Servicio técnico preventivo de hornos existentes',
        Decimal('200.00'),
        datetime(2026, 9, 8, 8, 0),
    ),
]


class Command(BaseCommand):
    help = 'Puebla gastos e inversiones iniciales (CU20) según Poblacion_4_Dias_Panaderia_Santiago.sql'

    def handle(self, *args, **options):
        if MovimientoEconomico.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {MovimientoEconomico.objects.count()} movimientos económicos registrados. No se aplicó el seed.'
                )
            )
            return

        usuario = (
            Usuario.objects.filter(nombre_usuario='csantiago').first()
            or Usuario.objects.filter(is_superuser=True).first()
            or Usuario.objects.first()
        )

        if not usuario:
            self.stdout.write(
                self.style.ERROR('No se encontró ningún usuario responsable. Ejecuta primero seed_usuarios.')
            )
            return

        with transaction.atomic():
            creados = 0
            for tipo, concepto, desc, monto, f_hora in GASTOS_DATA:
                MovimientoEconomico.objects.create(
                    id_usuario=usuario,
                    tipo=tipo,
                    concepto=concepto,
                    descripcion=desc,
                    monto=monto,
                    fecha_hora=timezone.make_aware(f_hora),
                )
                creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Poblado de Gastos e Inversiones completado: {creados} movimientos económicos registrados.'
            )
        )
