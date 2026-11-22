"""
Compras de demostración para el CU24 (Reporte de compras y gastos).

Cubre septiembre, octubre y noviembre de 2026, distribuidas en varios días
y proveedores. No altera el stock físico de inventario para que el reporte
pueda analizar volúmenes e importes con total fidelidad.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.compras.proveedores.models import Proveedor
from apps.productos_inventario.materia_prima.models import MateriaPrima

Usuario = get_user_model()


def _fecha(anio, mes, dia, hora=9):
    return timezone.make_aware(datetime(anio, mes, dia, hora, 0))


COMPRAS_DEMO = [
    # --- Septiembre 2026 ---
    (
        '2026-09-03',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('300.000'), Decimal('4.50')),
            ('Azúcar', Decimal('80.000'), Decimal('6.00')),
        ],
    ),
    (
        '2026-09-08',
        'Distribuidora Lácteos Santa Cruz',
        [
            ('Leche', Decimal('80.000'), Decimal('7.50')),
            ('Mantequilla', Decimal('20.000'), Decimal('35.00')),
            ('Huevos', Decimal('400.000'), Decimal('0.90')),
        ],
    ),
    (
        '2026-09-14',
        'Insumos y Levaduras Bolivia',
        [
            ('Levadura', Decimal('15.000'), Decimal('45.00')),
            ('Sal', Decimal('30.000'), Decimal('3.00')),
        ],
    ),
    (
        '2026-09-22',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('250.000'), Decimal('4.50')),
        ],
    ),
    # --- Octubre 2026 ---
    (
        '2026-10-04',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('350.000'), Decimal('4.50')),
            ('Azúcar', Decimal('100.000'), Decimal('6.00')),
        ],
    ),
    (
        '2026-10-11',
        'Distribuidora Lácteos Santa Cruz',
        [
            ('Leche', Decimal('100.000'), Decimal('7.50')),
            ('Mantequilla', Decimal('25.000'), Decimal('35.00')),
            ('Huevos', Decimal('500.000'), Decimal('0.90')),
        ],
    ),
    (
        '2026-10-18',
        'Insumos y Levaduras Bolivia',
        [
            ('Levadura', Decimal('20.000'), Decimal('45.00')),
            ('Sal', Decimal('40.000'), Decimal('3.00')),
        ],
    ),
    (
        '2026-10-26',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('300.000'), Decimal('4.50')),
            ('Azúcar', Decimal('50.000'), Decimal('6.00')),
        ],
    ),
    # --- Noviembre 2026 ---
    (
        '2026-11-02',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('400.000'), Decimal('4.50')),
            ('Azúcar', Decimal('120.000'), Decimal('6.00')),
        ],
    ),
    (
        '2026-11-09',
        'Distribuidora Lácteos Santa Cruz',
        [
            ('Leche', Decimal('120.000'), Decimal('7.50')),
            ('Mantequilla', Decimal('30.000'), Decimal('35.00')),
            ('Huevos', Decimal('600.000'), Decimal('0.90')),
        ],
    ),
    (
        '2026-11-16',
        'Insumos y Levaduras Bolivia',
        [
            ('Levadura', Decimal('25.000'), Decimal('45.00')),
            ('Sal', Decimal('50.000'), Decimal('3.00')),
        ],
    ),
    (
        '2026-11-20',
        'Molinos del Oriente S.R.L.',
        [
            ('Harina', Decimal('200.000'), Decimal('4.50')),
        ],
    ),
]


class Command(BaseCommand):
    help = 'Carga compras de demostración para el CU24 (septiembre a noviembre de 2026).'

    def handle(self, *args, **options):
        if Compra.objects.count() >= 10:
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {Compra.objects.count()} compras registradas. Omitiendo seed_compras_demo.'
                )
            )
            return

        usuario = (
            Usuario.objects.filter(nombre_usuario='csantiago').first()
            or Usuario.objects.filter(is_superuser=True).first()
            or Usuario.objects.first()
        )
        if not usuario:
            self.stdout.write(self.style.ERROR('No se encontró ningún usuario en la BD. Ejecuta seed_usuarios.'))
            return

        # Asegurar proveedores
        proveedores = {}
        for _, prov_nombre, _ in COMPRAS_DEMO:
            if prov_nombre not in proveedores:
                prov, _ = Proveedor.objects.get_or_create(
                    nombre=prov_nombre,
                    defaults={'telefono': '70011223', 'activo': True},
                )
                proveedores[prov_nombre] = prov

        # Mapeo de materias primas por nombre flexible
        materias_db = {m.nombre.lower(): m for m in MateriaPrima.objects.all()}

        creadas = 0
        with transaction.atomic():
            for fecha_str, prov_nombre, lineas in COMPRAS_DEMO:
                anio, mes, dia = map(int, fecha_str.split('-'))
                cuando = _fecha(anio, mes, dia)
                prov = proveedores[prov_nombre]

                # Calcular total
                total_compra = Decimal('0.00')
                lineas_a_crear = []
                for mat_nombre, cantidad, precio in lineas:
                    subtotal = cantidad * precio
                    total_compra += subtotal

                    # Buscar o crear materia prima
                    mat = materias_db.get(mat_nombre.lower())
                    if not mat:
                        # Buscar por coincidencia parcial
                        for k, v in materias_db.items():
                            if mat_nombre.lower() in k:
                                mat = v
                                break
                    if not mat:
                        mat = MateriaPrima.objects.create(
                            nombre=mat_nombre,
                            unidad_medida='kg' if mat_nombre != 'Leche' and mat_nombre != 'Huevos' else ('litros' if mat_nombre == 'Leche' else 'unidades'),
                            stock_minimo=Decimal('10.000'),
                            activo=True,
                        )
                        materias_db[mat_nombre.lower()] = mat

                    lineas_a_crear.append((mat, cantidad, precio, subtotal))

                compra = Compra.objects.create(
                    id_proveedor=prov,
                    id_usuario=usuario,
                    fecha_hora=cuando,
                    total=total_compra,
                )
                for mat, cantidad, precio, subtotal in lineas_a_crear:
                    DetalleCompra.objects.create(
                        id_compra=compra,
                        id_materia_prima=mat,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                    )
                creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Éxito: Se crearon {creadas} compras de demostración para el CU24 (septiembre a noviembre 2026).'
            )
        )
