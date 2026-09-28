from django.core.management.base import BaseCommand
from django.db import transaction
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso
from apps.usuarios_seguridad.users.models import Usuario


class Command(BaseCommand):
    help = 'Puebla la base de datos con los Roles, Permisos y Usuarios iniciales (Password: Admin123!)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando poblado de Usuarios y Seguridad...'))

        with transaction.atomic():
            # 1. Permisos
            permisos_data = [
                (1, 'gestionar_usuarios', 'Crear, editar, activar o inactivar usuarios del sistema'),
                (2, 'gestionar_productos', 'Registrar, editar y consultar productos y categorías'),
                (3, 'registrar_ventas', 'Registrar ventas directas por unidad'),
                (4, 'registrar_pedidos', 'Registrar pedidos y actualizar el estado de pedidos'),
                (5, 'registrar_produccion', 'Registrar cantidades producidas por jornada'),
                (6, 'gestionar_inventario', 'Consultar y ajustar existencias de materia prima y producto terminado'),
                (7, 'registrar_compras', 'Registrar compras a proveedores'),
                (8, 'gestionar_proveedores', 'Registrar y editar datos de proveedores'),
                (9, 'gestionar_gastos', 'Registrar gastos e inversiones del negocio'),
                (10, 'generar_reportes', 'Consultar y generar reportes administrativos y operativos'),
                (11, 'consultar_bitacora', 'Consultar el historial de acciones registradas en el sistema'),
            ]

            permisos_dict = {}
            for id_p, nombre, desc in permisos_data:
                permiso, _ = Permiso.objects.update_or_create(
                    id_permiso=id_p,
                    defaults={'nombre': nombre, 'descripcion': desc}
                )
                permisos_dict[id_p] = permiso

            # Se usa [OK] y no un símbolo de palomita a propósito: la consola de
            # Windows trabaja en cp1252 y no puede imprimir ese carácter, así que
            # el comando reventaba con UnicodeEncodeError. Como todo el seed está
            # dentro de un transaction.atomic(), eso además hacía que no se
            # guardara NADA, aunque los permisos ya se hubieran escrito.
            self.stdout.write(
                self.style.SUCCESS(f'[OK] {len(permisos_dict)} Permisos procesados.')
            )

            # 2. Roles
            roles_data = [
                (1, 'Administrador', 'Acceso total al sistema: gestión de usuarios, roles, permisos y configuración general'),
                (2, 'Propietario', 'Supervisión general del negocio, control financiero y acceso a reportes consolidados'),
                (3, 'Personal de Ventas', 'Registro de ventas, pedidos y atención al cliente en el mostrador'),
                (4, 'Personal de Producción', 'Registro de producción diaria y consulta de materias primas disponibles'),
            ]

            roles_dict = {}
            for id_r, nombre, desc in roles_data:
                rol, _ = Rol.objects.update_or_create(
                    id_rol=id_r,
                    defaults={'nombre': nombre, 'descripcion': desc}
                )
                roles_dict[id_r] = rol

            self.stdout.write(self.style.SUCCESS(f'[OK] {len(roles_dict)} Roles procesados.'))

            # 3. Rol - Permiso
            rol_permisos_map = {
                1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],  # Admin: Todos
                2: [2, 3, 4, 6, 7, 8, 9, 10, 11],        # Propietario: Todo menos gestionar usuarios
                3: [3, 4, 6, 10],                        # Ventas
                4: [5, 6],                               # Producción
            }

            for id_r, perm_ids in rol_permisos_map.items():
                rol = roles_dict[id_r]
                for id_p in perm_ids:
                    RolPermiso.objects.get_or_create(
                        rol=rol,
                        permiso=permisos_dict[id_p]
                    )

            self.stdout.write(self.style.SUCCESS('[OK] Mapeo de Roles y Permisos actualizado.'))

            # 4. Usuarios (Password común de prueba: Admin123!)
            #
            # Los correos siguen el patrón `apellido.rol@mail.com` y son cuentas de
            # prueba: no se envía correo real a nadie. En desarrollo el backend
            # SMTP apunta a Mailpit, que captura todo en localhost:8025, así que
            # `admin.global@mail.com` nunca sale a internet. En producción habría
            # que reemplazarlos por los correos reales de la panadería.
            default_password = 'Admin123!'
            usuarios_data = [
                (1, 1, 'admin', 'Soporte Técnico del Sistema', 'admin.global@mail.com', True, True),
                (2, 2, 'csantiago', 'Carlos Santiago Vargas', 'santiago.prop@mail.com', False, False),
                (3, 3, 'mgonzales', 'María Elena Gonzales Pérez', 'gonzales.ventas@mail.com', False, False),
                (4, 3, 'jrivera', 'Juana Rivera Quiroga', 'rivera.ventas@mail.com', False, False),
                (5, 4, 'mrojas', 'Miguel Ángel Rojas', 'rojas.produccion@mail.com', False, False),
                (6, 4, 'ptorrez', 'Pedro Torrez Salvatierra', 'torrez.produccion@mail.com', False, False),
            ]

            for id_u, id_r, username, nombre_comp, email, is_staff, is_super in usuarios_data:
                usuario, created = Usuario.objects.update_or_create(
                    nombre_usuario=username,
                    defaults={
                        'id_usuario': id_u,
                        'id_rol': roles_dict[id_r],
                        'nombre_completo': nombre_comp,
                        'email': email,
                        'activo': True,
                        'is_staff': is_staff,
                        'is_superuser': is_super,
                    }
                )
                usuario.set_password(default_password)
                usuario.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] {len(usuarios_data)} Usuarios creados/actualizados '
                    f'con contraseña "{default_password}".'
                )
            )
            self.stdout.write(
                self.style.SUCCESS('Poblado de seguridad completado exitosamente!')
            )
