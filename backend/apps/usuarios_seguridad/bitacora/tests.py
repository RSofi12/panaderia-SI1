"""
Pruebas del caso de uso CU26 — Gestionar bitácora.

    PruebasControlAcceso     ¿quién puede consultar la bitácora?
    PruebasSoloLectura       ¿se puede crear, editar o borrar una traza por la API?
    PruebasOrdenYDetalle     ¿el listado es cronológico y trae el detalle completo?
    PruebasFiltros           ¿filtra por fecha, usuario, módulo, acción y texto?
    PruebasOpciones          ¿los desplegables reciben los valores correctos?
    PruebasRegistroAutomatico  ¿una operación real deja su traza consultable?
"""
from datetime import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso
from apps.usuarios_seguridad.users.models import Usuario

CONTRASENA = 'PanADERIA2026!'


def momento(dia, hora=10):
    return timezone.make_aware(datetime(2026, 9, dia, hora, 0))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BasePruebaCU26(TestCase):
    def setUp(self):
        self.client = APIClient()

        consultar = Permiso.objects.create(id_permiso=11, nombre='consultar_bitacora')
        proveedores = Permiso.objects.create(id_permiso=8, nombre='gestionar_proveedores')
        ventas = Permiso.objects.create(id_permiso=3, nombre='registrar_ventas')

        rol_admin = Rol.objects.create(id_rol=1, nombre='Administrador')
        rol_propietario = Rol.objects.create(id_rol=2, nombre='Propietario')
        rol_ventas = Rol.objects.create(id_rol=3, nombre='Personal de Ventas')

        RolPermiso.objects.create(rol=rol_admin, permiso=consultar)
        RolPermiso.objects.create(rol=rol_admin, permiso=proveedores)
        RolPermiso.objects.create(rol=rol_propietario, permiso=consultar)
        RolPermiso.objects.create(rol=rol_ventas, permiso=ventas)

        self.admin = self._usuario('admin', 'Administrador de Prueba', rol_admin)
        self.propietario = self._usuario('csantiago', 'Carlos Santiago Vargas', rol_propietario)
        self.vendedor = self._usuario('mgonzales', 'María Elena Gonzales', rol_ventas)

        self.inicio_sesion = Bitacora.objects.create(
            usuario=self.vendedor, accion=AccionBitacora.INICIO_SESION,
            tabla_afectada='usuario', descripcion='Inicio de sesión exitoso',
            agente_usuario='Mozilla/5.0 (Windows NT 10.0)', fecha_hora=momento(1),
        )
        self.alta_producto = Bitacora.objects.create(
            usuario=self.propietario, accion=AccionBitacora.ALTA_PRODUCTO,
            tabla_afectada='producto', descripcion='Alta del producto Marraqueta',
            fecha_hora=momento(5),
        )
        self.login_fallido = Bitacora.objects.create(
            usuario=None, nombre_usuario_intento='intruso', accion=AccionBitacora.LOGIN_FALLIDO,
            tabla_afectada='usuario', descripcion='Contraseña incorrecta',
            fecha_hora=momento(10),
        )

        self.url_lista = reverse('bitacora:lista')
        self.url_opciones = reverse('bitacora:opciones')

    def _usuario(self, nombre_usuario, nombre_completo, rol):
        return Usuario.objects.create_user(
            nombre_usuario=nombre_usuario,
            password=CONTRASENA,
            nombre_completo=nombre_completo,
            email=f'{nombre_usuario}@mail.com',
            id_rol=rol,
        )

    def como(self, usuario):
        self.client.force_authenticate(user=usuario)
        return self.client

    def ids(self, respuesta):
        return [fila['id_bitacora'] for fila in respuesta.data['results']]


class PruebasControlAcceso(BasePruebaCU26):
    def test_sin_sesion_responde_401(self):
        self.assertEqual(self.client.get(self.url_lista).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_administrador_consulta(self):
        self.assertEqual(self.como(self.admin).get(self.url_lista).status_code, status.HTTP_200_OK)

    def test_propietario_consulta(self):
        self.assertEqual(self.como(self.propietario).get(self.url_lista).status_code, status.HTTP_200_OK)

    def test_personal_de_ventas_recibe_403(self):
        cliente = self.como(self.vendedor)
        self.assertEqual(cliente.get(self.url_lista).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(cliente.get(self.url_opciones).status_code, status.HTTP_403_FORBIDDEN)


class PruebasSoloLectura(BasePruebaCU26):
    def test_ningun_metodo_de_escritura_existe(self):
        cliente = self.como(self.admin)
        cuerpo = {'accion': AccionBitacora.ALTA_PRODUCTO, 'descripcion': 'falsa'}
        for metodo in (cliente.post, cliente.put, cliente.patch, cliente.delete):
            with self.subTest(metodo=metodo.__name__):
                self.assertEqual(
                    metodo(self.url_lista, cuerpo, format='json').status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )
        self.assertEqual(Bitacora.objects.count(), 3)


class PruebasOrdenYDetalle(BasePruebaCU26):
    def test_orden_cronologico_del_mas_reciente(self):
        respuesta = self.como(self.admin).get(self.url_lista)
        self.assertEqual(
            self.ids(respuesta),
            [self.login_fallido.pk, self.alta_producto.pk, self.inicio_sesion.pk],
        )

    def test_detalle_trae_usuario_etiqueta_y_navegador(self):
        fila = next(
            f for f in self.como(self.admin).get(self.url_lista).data['results']
            if f['id_bitacora'] == self.inicio_sesion.pk
        )
        self.assertEqual(fila['id_usuario'], self.vendedor.pk)
        self.assertEqual(fila['nombre_usuario'], 'mgonzales')
        self.assertEqual(fila['nombre_completo'], 'María Elena Gonzales')
        self.assertEqual(fila['accion_etiqueta'], 'Inicio de sesión')
        self.assertEqual(fila['agente_usuario'], 'Mozilla/5.0 (Windows NT 10.0)')

    def test_intento_sin_usuario_conserva_el_nombre_digitado(self):
        fila = self.como(self.admin).get(self.url_lista).data['results'][0]
        self.assertIsNone(fila['id_usuario'])
        self.assertIsNone(fila['nombre_usuario'])
        self.assertEqual(fila['nombre_usuario_intento'], 'intruso')

    def test_listado_paginado(self):
        for dia in range(11, 23):
            Bitacora.objects.create(accion=AccionBitacora.CIERRE_SESION, fecha_hora=momento(dia))
        respuesta = self.como(self.admin).get(self.url_lista)
        self.assertEqual(respuesta.data['count'], 15)
        self.assertEqual(len(respuesta.data['results']), 10)
        self.assertIsNotNone(respuesta.data['next'])


class PruebasFiltros(BasePruebaCU26):
    def consultar(self, **filtros):
        return self.como(self.admin).get(self.url_lista, filtros)

    def test_rango_de_fechas_inclusivo(self):
        respuesta = self.consultar(fecha_desde='2026-09-05', fecha_hasta='2026-09-10')
        self.assertEqual(self.ids(respuesta), [self.login_fallido.pk, self.alta_producto.pk])

    def test_por_usuario(self):
        respuesta = self.consultar(usuario=self.propietario.pk)
        self.assertEqual(self.ids(respuesta), [self.alta_producto.pk])

    def test_por_modulo(self):
        respuesta = self.consultar(modulo='producto')
        self.assertEqual(self.ids(respuesta), [self.alta_producto.pk])

    def test_por_accion(self):
        respuesta = self.consultar(accion=AccionBitacora.LOGIN_FALLIDO)
        self.assertEqual(self.ids(respuesta), [self.login_fallido.pk])

    def test_texto_en_descripcion_y_usuario(self):
        self.assertEqual(self.ids(self.consultar(q='marraqueta')), [self.alta_producto.pk])
        self.assertEqual(self.ids(self.consultar(q='intruso')), [self.login_fallido.pk])

    def test_filtros_combinados(self):
        respuesta = self.consultar(modulo='usuario', fecha_hasta='2026-09-05')
        self.assertEqual(self.ids(respuesta), [self.inicio_sesion.pk])

    def test_valores_invalidos_responden_400(self):
        casos = [
            {'fecha_desde': '05/09/2026'},
            {'fecha_desde': '2026-02-30'},
            {'fecha_desde': '2026-09-10', 'fecha_hasta': '2026-09-01'},
            {'usuario': 'abc'},
            {'accion': 'NO_EXISTE'},
        ]
        for filtros in casos:
            with self.subTest(filtros=filtros):
                self.assertEqual(self.consultar(**filtros).status_code, status.HTTP_400_BAD_REQUEST)


class PruebasOpciones(BasePruebaCU26):
    def test_opciones_para_los_filtros(self):
        datos = self.como(self.propietario).get(self.url_opciones).data
        self.assertEqual(len(datos['acciones']), len(AccionBitacora.choices))
        self.assertIn({'valor': 'ALTA_PRODUCTO', 'etiqueta': 'Alta de producto'}, datos['acciones'])
        self.assertEqual(datos['modulos'], ['producto', 'usuario'])
        self.assertEqual(
            [u['nombre_usuario'] for u in datos['usuarios']],
            ['csantiago', 'mgonzales'],
        )


class PruebasRegistroAutomatico(BasePruebaCU26):
    def test_alta_de_proveedor_queda_consultable(self):
        cliente = self.como(self.admin)
        alta = cliente.post('/api/proveedores/', {
            'nombre': 'Harinas del Norte', 'telefono': '33445566', 'direccion': 'Av. Cumavi',
        }, format='json')
        self.assertEqual(alta.status_code, status.HTTP_201_CREATED)

        respuesta = cliente.get(self.url_lista, {'accion': AccionBitacora.ALTA_PROVEEDOR})
        self.assertEqual(respuesta.data['count'], 1)
        fila = respuesta.data['results'][0]
        self.assertEqual(fila['nombre_usuario'], 'admin')
        self.assertEqual(fila['tabla_afectada'], 'proveedor')
        self.assertIn('Harinas del Norte', fila['descripcion'])
