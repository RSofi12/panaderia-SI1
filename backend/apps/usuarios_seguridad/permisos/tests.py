"""
Pruebas del catálogo de permisos (CU4 — Asignar roles y permisos).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()
CONTRASENA_TEST = 'TestAdmin123!'


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class PermisosCatalogTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.permiso_cu4 = Permiso.objects.create(
            nombre='asignar_permisos',
            modulo=ModuloPermiso.USUARIOS_SEGURIDAD,
            descripcion='Permiso CU4',
        )
        self.permiso_ventas = Permiso.objects.create(
            nombre='registrar_ventas',
            modulo=ModuloPermiso.COMERCIALIZACION,
            descripcion='Permiso ventas',
        )

        self.rol_admin = Rol.objects.create(nombre='Administrador')
        self.rol_ventas = Rol.objects.create(nombre='Personal de Ventas')

        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.permiso_cu4)
        RolPermiso.objects.create(rol=self.rol_ventas, permiso=self.permiso_ventas)

        self.user_admin = Usuario.objects.create_user(
            nombre_usuario='admin_test',
            password=CONTRASENA_TEST,
            nombre_completo='Admin Test',
            email='admin@test.com',
            id_rol=self.rol_admin,
        )
        self.user_ventas = Usuario.objects.create_user(
            nombre_usuario='ventas_test',
            password=CONTRASENA_TEST,
            nombre_completo='Ventas Test',
            email='ventas@test.com',
            id_rol=self.rol_ventas,
        )

    def test_catalogo_permisos_sin_autenticacion_retorna_401(self):
        res = self.client.get('/api/permisos/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_catalogo_permisos_sin_permiso_cu4_retorna_403(self):
        self.client.force_authenticate(user=self.user_ventas)
        res = self.client.get('/api/permisos/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalogo_permisos_con_permiso_cu4_retorna_lista_con_modulo(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.get('/api/permisos/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        datos = res.json()
        self.assertGreaterEqual(len(datos), 2)
        nombres = [p['nombre'] for p in datos]
        self.assertIn('asignar_permisos', nombres)
        self.assertIn('registrar_ventas', nombres)

        primer_permiso = datos[0]
        self.assertIn('id_permiso', primer_permiso)
        self.assertIn('nombre', primer_permiso)
        self.assertIn('modulo', primer_permiso)
        self.assertIn('modulo_display', primer_permiso)

    def test_catalogo_permisos_agrupados_por_modulo(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.get('/api/permisos/agrupados/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        datos = res.json()
        modulos = [grupo['modulo'] for grupo in datos]
        self.assertIn('usuarios_seguridad', modulos)
        self.assertIn('comercializacion', modulos)
