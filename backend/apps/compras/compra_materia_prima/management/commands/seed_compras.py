"""
Comando de poblado de compras de materia prima (CU7).
Puebla las compras iniciales de prueba según docs/informes/Poblacion_4_Dias_Panaderia_Santiago.sql.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.compras.models import Proveedor
from apps.compras.compra_materia_prima.models import Compra
from apps.compras.compra_materia_prima.services.registrar_compra import registrar_compra
from apps.productos_inventario.models import MateriaPrima

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla compras iniciales de materia prima (CU7) según Poblacion_4_Dias_Panaderia_Santiago.sql'

    def handle(self, *args, **options):
        if Compra.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existen {Compra.objects.count()} compra(s) registradas. No se aplicó el seed.'
                )
            )
            return

        usuario = Usuario.objects.filter(nombre_usuario='csantiago').first() or Usuario.objects.filter(is_superuser=True).first()
        if not usuario:
            self.stdout.write(
                self.style.ERROR('No se encontró el usuario csantiago ni un administrador. Ejecuta primero seed_usuarios.')
            )
            return

        proveedores = {p.nombre: p for p in Proveedor.objects.all()}
        materias = {m.nombre: m for m in MateriaPrima.objects.all()}

        if not proveedores or not materias:
            self.stdout.write(
                self.style.ERROR(
                    'Faltan proveedores o materias primas. Ejecuta antes seed_proveedores y seed_materias_primas.'
                )
            )
            return

        compras_simuladas = [
            {
                'proveedor': 'Molinos del Oriente S.R.L.',
                'detalles': [
                    {'materia': 'Harina', 'cantidad': '200.000', 'precio': '4.50'},
                    {'materia': 'Sal', 'cantidad': '20.000', 'precio': '3.00'},
                    {'materia': 'Azúcar', 'cantidad': '50.000', 'precio': '6.00'},
                ],
            },
            {
                'proveedor': 'Distribuidora Lácteos Santa Cruz',
                'detalles': [
                    {'materia': 'Leche', 'cantidad': '60.000', 'precio': '7.50'},
                    {'materia': 'Mantequilla', 'cantidad': '15.000', 'precio': '35.00'},
                    {'materia': 'Huevos', 'cantidad': '300.000', 'precio': '0.90'},
                ],
            },
            {
                'proveedor': 'Insumos y Levaduras Bolivia',
                'detalles': [
                    {'materia': 'Levadura', 'cantidad': '10.000', 'precio': '45.00'},
                ],
            },
        ]

        with transaction.atomic():
            creadas = 0
            for c_data in compras_simuladas:
                prov = proveedores.get(c_data['proveedor'])
                if not prov:
                    continue

                lineas = []
                for det in c_data['detalles']:
                    mp = materias.get(det['materia'])
                    if mp:
                        lineas.append({
                            'id_materia_prima': mp.id_materia_prima,
                            'cantidad': det['cantidad'],
                            'precio_unitario': det['precio'],
                        })

                if lineas:
                    compra = registrar_compra(
                        usuario=usuario,
                        id_proveedor=prov.id_proveedor,
                        lineas=lineas,
                        agente_usuario='seed_compras',
                    )
                    creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [OK] Compra #{compra.id_compra} registrada — {prov.nombre} — Total: Bs {compra.total}'
                        )
                    )

        self.stdout.write(self.style.SUCCESS(f'Poblado completado: {creadas} compras registradas exitosamente.'))
