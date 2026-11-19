"""
Comando Maestro de Poblado (Seed Master) — Panadería Santiago (SI-1).
Ejecuta de manera secuencial, ordenada e idempotente todos los seeders del sistema.

Uso:
    python manage.py seed_all
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Ejecuta todos los seeders en orden de dependencias para poblar '
        'completamente la base de datos de Panadería Santiago.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIME(
            '============================================================\n'
            '  INICIANDO POBLADO MAESTRO — PANADERÍA SANTIAGO (SI-1)    \n'
            '============================================================'
        ) if hasattr(self.style, 'MIME') else self.style.NOTICE(
            '============================================================\n'
            '  INICIANDO POBLADO MAESTRO — PANADERÍA SANTIAGO (SI-1)    \n'
            '============================================================'
        ))

        # Lista ordenada de comandos: (nombre_comando, descripcion)
        seeders = [
            ('seed_usuarios', '1. Usuarios, Roles y Permisos (Seguridad)'),
            ('seed_materias_primas', '2. Catálogo de Materias Primas e Insumos'),
            ('seed_productos', '3. Catálogo de Panes y Categorías'),
            ('seed_recetas', '4. Fórmulas / Recetas de Producción (BOM/MRP)'),
            ('seed_proveedores', '5. Proveedores de Insumos'),
            ('seed_compras', '6. Compras y Entradas de Materia Prima'),
            ('seed_existencias', '7. Existencias Iniciales de Pan en Mostrador'),
            ('seed_historial_demo', '8. Jornadas de Producción Diaria y Mermas'),
            ('seed_pedidos_demo', '9. Clientes y Pedidos en Mostrador/Anticipados'),
            ('seed_gastos_demo', '10. Gastos Operativos e Inversiones'),
            ('seed_ventas_demo', '11. Registro Histórico de Ventas'),
            ('seed_mes_operativo', '12. Simulación de 1 Mes Operativo Completo (L-S, 8h)'),
        ]

        exitos = 0
        errores = 0

        for comando, descripcion in seeders:
            self.stdout.write(self.style.NOTICE(f'\n>>> Ejecutando {descripcion} ({comando})...'))
            try:
                call_command(comando)
                exitos += 1
            except CommandError as ce:
                self.stdout.write(self.style.WARNING(f'  [AVISO / OMITIDO] {ce}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] Falló {comando}: {e}'))
                errores += 1

        self.stdout.write('\n' + '=' * 60)
        if errores == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'POBLADO MAESTRO COMPLETADO EXITOSAMENTE ({exitos}/{len(seeders)} seeders procesados).'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'POBLADO FINALIZADO CON OBSERVACIONES: {exitos} exitosos, {errores} errores.'
                )
            )
        self.stdout.write('=' * 60 + '\n')
