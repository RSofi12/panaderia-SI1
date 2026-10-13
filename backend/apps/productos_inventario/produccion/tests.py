"""
Pruebas base de la sub-app de Producción (CU10, CU11).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasBaseProduccion(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.rol_produccion = Rol.objects.create(
            nombre='Personal de Producción',
            descripcion='Registro de producción diaria y consulta del historial'
        )
        self.permiso_produccion = Permiso.objects.create(
            nombre='registrar_produccion',
            modulo='productos_inventario',
            descripcion='Registrar cantidades producidas por jornada'
        )
        self.rol_produccion.permisos.add(self.permiso_produccion)

        self.usuario = Usuario.objects.create_user(
            nombre_usuario='panadero',
            password='PanADERIA2026!',
            nombre_completo='Pedro Panadero',
            email='panadero.prueba@mail.com',
            id_rol=self.rol_produccion,
        )

        self.rol_sin_permiso = Rol.objects.create(
            nombre='Personal de Ventas',
            descripcion='No tiene permisos para consultar producción'
        )
        self.usuario_sin_permiso = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password='PanADERIA2026!',
            nombre_completo='Ana Vendedor',
            email='vendedor.prueba@mail.com',
            id_rol=self.rol_sin_permiso,
        )

    def test_listado_produccion_requiere_autenticacion(self):
        respuesta = self.client.get('/api/produccion/')
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listado_produccion_requiere_permiso_de_produccion(self):
        self.client.force_authenticate(user=self.usuario_sin_permiso)
        respuesta = self.client.get('/api/produccion/')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_listado_produccion_autenticado_con_permiso_responde_200(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/produccion/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)

    def test_usuario_con_gestionar_productos_puede_consultar_historial(self):
        rol_admin = Rol.objects.create(nombre='Administrador', descripcion='Gestión de inventario y productos')
        permiso_admin = Permiso.objects.create(
            nombre='gestionar_productos',
            modulo='productos_inventario',
            descripcion='Gestión de catálogo y productos'
        )
        rol_admin.permisos.add(permiso_admin)
        usuario_admin = Usuario.objects.create_user(
            nombre_usuario='admin_user',
            password='PanADERIA2026!',
            nombre_completo='Carlos Admin',
            email='admin@mail.com',
            id_rol=rol_admin,
        )
        self.client.force_authenticate(user=usuario_admin)
        respuesta = self.client.get('/api/produccion/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_rango_fechas_invalido_responde_400(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/produccion/?fecha_desde=2026-10-15&fecha_hasta=2026-10-10')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_desde', respuesta.data)

    def test_formato_fecha_invalido_responde_400(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/produccion/?fecha_desde=invalida')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_desde', respuesta.data)

    def test_id_producto_invalido_responde_400(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/produccion/?id_producto=no_es_numero')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('id_producto', respuesta.data)

