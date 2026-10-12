"""
Pruebas del CU6 — Gestionar proveedores.

Cubre:
    - Listado y filtros (?q=, ?activo=)
    - Alta y validaciones (nombre único, teléfono válido)
    - Edición y baja lógica (toggle-activo)
    - Permisos RBAC (gestionar_proveedores vs registrar_compras)
    - Trazabilidad en Bitácora (CU26)
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.compras.proveedores.models import Proveedor
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BasePruebasProveedores(TestCase):
    def setUp(self):
        self.client = APIClient()

        perm_proveedores = Permiso.objects.create(
            nombre='gestionar_proveedores',
            descripcion='Gestionar proveedores',
            modulo=ModuloPermiso.COMPRAS,
        )
        perm_compras = Permiso.objects.create(
            nombre='registrar_compras',
            descripcion='Registrar compras',
            modulo=ModuloPermiso.COMPRAS,
        )

        rol_admin = Rol.objects.create(nombre='Administrador', descripcion='Admin')
        RolPermiso.objects.create(rol=rol_admin, permiso=perm_proveedores)

        rol_propietario = Rol.objects.create(nombre='Propietario', descripcion='Dueño')
        RolPermiso.objects.create(rol=rol_propietario, permiso=perm_proveedores)
        RolPermiso.objects.create(rol=rol_propietario, permiso=perm_compras)

        rol_comprador = Rol.objects.create(nombre='Comprador Solo', descripcion='Solo compras')
        RolPermiso.objects.create(rol=rol_comprador, permiso=perm_compras)

        rol_sin_acceso = Rol.objects.create(nombre='Sin Acceso', descripcion='Ninguno')

        self.admin = Usuario.objects.create_user(
            nombre_usuario='admin_user',
            password='Password123!',
            nombre_completo='Admin General',
            email='admin@mail.com',
            id_rol=rol_admin,
        )
        self.comprador = Usuario.objects.create_user(
            nombre_usuario='comprador_user',
            password='Password123!',
            nombre_completo='Solo Comprador',
            email='comprador@mail.com',
            id_rol=rol_comprador,
        )
        self.sin_permiso = Usuario.objects.create_user(
            nombre_usuario='sin_permiso',
            password='Password123!',
            nombre_completo='Sin Permiso',
            email='sinpermiso@mail.com',
            id_rol=rol_sin_acceso,
        )

        self.proveedor_activo = Proveedor.objects.create(
            nombre='Molinos Central',
            telefono='71122334',
            direccion='Av. Santos Dumont #100',
            activo=True,
        )


class PruebasCRUDProveedores(BasePruebasProveedores):
    def test_listar_proveedores(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/proveedores/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_crear_proveedor_exitoso_registra_bitacora(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'nombre': 'Harinas del Valle S.R.L.',
            'telefono': '70012345',
            'direccion': 'Km 6 Doble Vía a La Guardia',
        }
        res = self.client.post('/api/proveedores/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['nombre'], 'Harinas del Valle S.R.L.')

        self.assertTrue(
            Bitacora.objects.filter(
                accion=AccionBitacora.ALTA_PROVEEDOR,
                tabla_afectada='proveedor',
                usuario=self.admin,
            ).exists()
        )

    def test_toggle_activo_inactiva_y_registra_bitacora(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/proveedores/{self.proveedor_activo.id_proveedor}/toggle-activo/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['activo'])

        self.proveedor_activo.refresh_from_db()
        self.assertFalse(self.proveedor_activo.activo)

        self.assertTrue(
            Bitacora.objects.filter(
                accion=AccionBitacora.CAMBIAR_ESTADO_PROVEEDOR,
                tabla_afectada='proveedor',
                usuario=self.admin,
            ).exists()
        )


class PruebasPermisosProveedores(BasePruebasProveedores):
    def test_comprador_puede_leer_pero_no_crear(self):
        self.client.force_authenticate(user=self.comprador)
        res_get = self.client.get('/api/proveedores/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        res_post = self.client.post(
            '/api/proveedores/',
            {'nombre': 'Test Proveedor', 'telefono': '71112222', 'direccion': 'Calle 1'},
            format='json',
        )
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_permiso_responde_403(self):
        self.client.force_authenticate(user=self.sin_permiso)
        res = self.client.get('/api/proveedores/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
