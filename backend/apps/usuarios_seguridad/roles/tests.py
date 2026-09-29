"""
Pruebas integrales del caso de uso CU04 — Asignar roles y permisos (Backend).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()
CONTRASENA_TEST = 'PanaderiaTest2026!'


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class RolesYMatrizCU4Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Permisos base
        self.permiso_cu4 = Permiso.objects.create(
            nombre='asignar_permisos',
            modulo=ModuloPermiso.USUARIOS_SEGURIDAD,
            descripcion='Permiso CU4 para matriz y roles',
        )
        self.permiso_usuarios = Permiso.objects.create(
            nombre='gestionar_usuarios',
            modulo=ModuloPermiso.USUARIOS_SEGURIDAD,
            descripcion='Permiso CU3',
        )
        self.permiso_ventas = Permiso.objects.create(
            nombre='registrar_ventas',
            modulo=ModuloPermiso.COMERCIALIZACION,
            descripcion='Permiso ventas',
        )
        self.permiso_productos = Permiso.objects.create(
            nombre='gestionar_productos',
            modulo=ModuloPermiso.PRODUCTOS_INVENTARIO,
            descripcion='Permiso productos',
        )

        # Roles base
        self.rol_admin = Rol.objects.create(
            nombre='Administrador',
            descripcion='Rol administrador base'
        )
        self.rol_ventas = Rol.objects.create(
            nombre='Personal de Ventas',
            descripcion='Rol ventas base'
        )

        # Asignaciones iniciales
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.permiso_cu4)
        RolPermiso.objects.create(rol=self.rol_admin, permiso=self.permiso_usuarios)
        RolPermiso.objects.create(rol=self.rol_ventas, permiso=self.permiso_ventas)

        # Usuarios de prueba
        self.user_admin = Usuario.objects.create_user(
            nombre_usuario='admin_cu4',
            password=CONTRASENA_TEST,
            nombre_completo='Administrador CU4',
            email='admincu4@mail.com',
            id_rol=self.rol_admin,
        )
        self.user_ventas = Usuario.objects.create_user(
            nombre_usuario='ventas_cu4',
            password=CONTRASENA_TEST,
            nombre_completo='Ventas CU4',
            email='ventascu4@mail.com',
            id_rol=self.rol_ventas,
        )

    def test_roles_sin_autenticacion_retorna_401(self):
        res = self.client.get('/api/roles/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_roles_sin_permiso_cu4_retorna_403(self):
        self.client.force_authenticate(user=self.user_ventas)
        res = self.client.get('/api/roles/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_listar_roles_retorna_metricas_y_roles_protegidos(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.get('/api/roles/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        datos = res.json()
        self.assertGreaterEqual(len(datos), 2)

        rol_admin_data = next(r for r in datos if r['id_rol'] == self.rol_admin.id_rol)
        self.assertTrue(rol_admin_data['es_protegido'])
        self.assertEqual(rol_admin_data['total_usuarios'], 1)
        self.assertEqual(rol_admin_data['total_permisos'], 2)

    def test_detalle_rol_incluye_permisos_completos(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.get(f'/api/roles/{self.rol_admin.id_rol}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        datos = res.json()
        self.assertEqual(datos['id_rol'], self.rol_admin.id_rol)
        nombres_permisos = [p['nombre'] for p in datos['permisos']]
        self.assertIn('asignar_permisos', nombres_permisos)
        self.assertIn('gestionar_usuarios', nombres_permisos)

    def test_crear_rol_exitoso_y_audita_en_bitacora(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.post('/api/roles/', {
            'nombre': 'Supervisor de Turno',
            'descripcion': 'Supervisa la panadería en turno vespertino',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        datos = res.json()
        self.assertEqual(datos['nombre'], 'Supervisor de Turno')
        self.assertFalse(datos['es_protegido'])

        # Verificar Bitácora
        bitacora = Bitacora.objects.filter(accion=AccionBitacora.ALTA_ROL).latest('id_bitacora')
        self.assertIn('Supervisor de Turno', bitacora.descripcion)
        self.assertEqual(bitacora.usuario, self.user_admin)

    def test_crear_rol_nombre_duplicado_es_rechazado(self):
        self.client.force_authenticate(user=self.user_admin)
        # Intento de crear rol con nombre en minúsculas 'administrador'
        res = self.client.post('/api/roles/', {
            'nombre': 'administrador',
            'descripcion': 'Duplicado',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_editar_descripcion_rol_exitoso_y_audita(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.patch(f'/api/roles/{self.rol_ventas.id_rol}/', {
            'descripcion': 'Descripción actualizada de ventas',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.rol_ventas.refresh_from_db()
        self.assertEqual(self.rol_ventas.descripcion, 'Descripción actualizada de ventas')

        # Verificar Bitácora
        bitacora = Bitacora.objects.filter(accion=AccionBitacora.EDICION_ROL).latest('id_bitacora')
        self.assertIn(self.rol_ventas.nombre, bitacora.descripcion)

    def test_editar_nombre_rol_protegido_es_rechazado(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.patch(f'/api/roles/{self.rol_admin.id_rol}/', {
            'nombre': 'SuperAdmin',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('protegido', str(res.json()))

    def test_delete_rol_retorna_405_method_not_allowed(self):
        self.client.force_authenticate(user=self.user_admin)
        res = self.client.delete(f'/api/roles/{self.rol_ventas.id_rol}/')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_asignar_y_quitar_permiso_individual(self):
        self.client.force_authenticate(user=self.user_admin)

        # Asignar 'gestionar_productos' a Personal de Ventas
        res = self.client.post(f'/api/roles/{self.rol_ventas.id_rol}/permisos/asignar/', {
            'id_permiso': self.permiso_productos.id_permiso,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.rol_ventas.permisos.filter(pk=self.permiso_productos.pk).exists())

        # Verificar auditoría de asignación
        bitacora_asig = Bitacora.objects.filter(accion=AccionBitacora.ASIGNAR_PERMISO_ROL).latest('id_bitacora')
        self.assertIn(self.permiso_productos.nombre, bitacora_asig.descripcion)

        # Quitar el permiso asignado
        res_quitar = self.client.post(f'/api/roles/{self.rol_ventas.id_rol}/permisos/quitar/', {
            'id_permiso': self.permiso_productos.id_permiso,
        }, format='json')
        self.assertEqual(res_quitar.status_code, status.HTTP_200_OK)
        self.assertFalse(self.rol_ventas.permisos.filter(pk=self.permiso_productos.pk).exists())

        # Verificar auditoría de revocación
        bitacora_rev = Bitacora.objects.filter(accion=AccionBitacora.REVOCAR_PERMISO_ROL).latest('id_bitacora')
        self.assertIn(self.permiso_productos.nombre, bitacora_rev.descripcion)

    def test_reemplazar_matriz_permisos_exitoso_y_audita(self):
        self.client.force_authenticate(user=self.user_admin)

        # Reemplazar permisos de Ventas con [registrar_ventas, gestionar_productos]
        nuevos_ids = [self.permiso_ventas.id_permiso, self.permiso_productos.id_permiso]
        res = self.client.put(f'/api/roles/{self.rol_ventas.id_rol}/permisos/', {
            'permisos': nuevos_ids,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        permisos_actuales = list(self.rol_ventas.permisos.values_list('id_permiso', flat=True))
        self.assertCountEqual(permisos_actuales, nuevos_ids)

        # Verificar Bitácora con diff
        bitacora = Bitacora.objects.filter(accion=AccionBitacora.ACTUALIZACION_MATRIZ_PERMISOS).latest('id_bitacora')
        self.assertIn('gestionar_productos', bitacora.descripcion)

    def test_guarda_anti_autobloqueo_rol_administrador(self):
        self.client.force_authenticate(user=self.user_admin)

        # Intentar actualizar la matriz del rol Administrador quitándole 'asignar_permisos'
        res = self.client.put(f'/api/roles/{self.rol_admin.id_rol}/permisos/', {
            'permisos': [self.permiso_usuarios.id_permiso],  # falta permiso_cu4
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('asignar_permisos', str(res.json()))

    def test_guarda_anti_autobloqueo_quitar_permiso_individual_de_admin(self):
        self.client.force_authenticate(user=self.user_admin)

        # Intentar quitar puntualmente 'asignar_permisos' de Administrador
        res = self.client.post(f'/api/roles/{self.rol_admin.id_rol}/permisos/quitar/', {
            'id_permiso': self.permiso_cu4.id_permiso,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revocacion_de_permiso_surte_efecto_inmediato(self):
        """
        Test dinámico de regresión:
        Verifica que revocar un permiso a un rol bloquea el acceso en la petición
        inmediatamente posterior del usuario, ya que DRF evalúa contra la BD.
        """
        # 1. Asignamos 'gestionar_usuarios' al rol de ventas
        self.rol_ventas.asignar_permiso(self.permiso_usuarios)

        # 2. El usuario de ventas ahora puede consultar /api/usuarios/
        client_ventas = APIClient()
        client_ventas.force_authenticate(user=self.user_ventas)
        res_ok = client_ventas.get('/api/usuarios/')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)

        # 3. El Administrador revoca 'gestionar_usuarios' del rol de ventas
        self.client.force_authenticate(user=self.user_admin)
        res_rev = self.client.post(f'/api/roles/{self.rol_ventas.id_rol}/permisos/quitar/', {
            'id_permiso': self.permiso_usuarios.id_permiso,
        }, format='json')
        self.assertEqual(res_rev.status_code, status.HTTP_200_OK)

        # 4. Inmediatamente el cliente de ventas vuelve a pedir /api/usuarios/ y recibe 403
        res_bloqueado = client_ventas.get('/api/usuarios/')
        self.assertEqual(res_bloqueado.status_code, status.HTTP_403_FORBIDDEN)
