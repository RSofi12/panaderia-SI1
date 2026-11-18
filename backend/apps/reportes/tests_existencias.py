"""CU23: precisión, filtros, autorización JWT y consulta sin efectos secundarios."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.productos_inventario.materia_prima.models import (
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
)
from apps.productos_inventario.materia_prima.selectors import (
    obtener_materias_primas_bajo_stock,
)
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
)
from apps.productos_inventario.productos_terminados.serializers import (
    InventarioProductoTerminadoSerializer,
)
from apps.reportes.services.reporte_existencias import reporte_existencias
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso


Usuario = get_user_model()
RESUMEN_VACIO = {
    'total': 0,
    'materias_primas': 0,
    'productos_terminados': 0,
    'bajo_stock': 0,
    'sin_inventario': 0,
}


class DatosExistencias:
    """Catálogos deliberadamente distintos: no confundir cero con inventario ausente."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.harina = cls.crear_materia('Harina', '9.999', '10.000')
        cls.azucar = cls.crear_materia('Azucar', '10.000', '10.000')
        cls.sal = cls.crear_materia('Sal', '10.001', '10.000')
        cls.agua = cls.crear_materia('Agua', '0.000', '0.000', unidad='litros')
        cls.levadura = cls.crear_materia('Levadura', '0.001', '0.002')
        cls.avena = cls.crear_materia('Avena', '2.000', '3.000', activo=False)
        cls.manteca = cls.crear_materia('Manteca', None, '5.000')
        cls.pan_integral = cls.crear_producto('Pan integral', 19)
        cls.pan_blanco = cls.crear_producto('Pan blanco', 20)
        cls.pan_harina = cls.crear_producto('Pan de harina', 21)
        cls.pan_inactivo = cls.crear_producto('Pan de ayer', 5, activo=False)
        cls.cunape = cls.crear_producto('Cunape', None)

        # Los snapshots también verifican movimientos reales, no solo tablas vacías.
        MovimientoMateriaPrima.objects.create(
            id_inventario=cls.harina.inventario,
            tipo='entrada',
            cantidad=Decimal('1.000'),
        )
        MovimientoProductoTerminado.objects.create(
            id_inventario=cls.pan_integral.inventario_terminado,
            tipo='entrada',
            cantidad=1,
        )

    @staticmethod
    def crear_materia(nombre, stock, minimo='0.000', *, activo=True, unidad='kg'):
        materia = MateriaPrima.objects.create(
            nombre=nombre,
            unidad_medida=unidad,
            stock_minimo=Decimal(minimo),
            activo=activo,
        )
        if stock is not None:
            InventarioMateriaPrima.objects.create(
                id_materia_prima=materia,
                stock_actual=Decimal(stock),
            )
        return materia

    @staticmethod
    def crear_producto(nombre, stock, *, activo=True):
        producto = Producto.objects.create(
            nombre=nombre,
            precio_venta=Decimal('1.00'),
            activo=activo,
        )
        if stock is not None:
            InventarioProductoTerminado.objects.create(
                id_producto=producto,
                stock_actual=stock,
            )
        return producto

    def setUp(self):
        super().setUp()
        cache.clear()

    def snapshot_inventario(self):
        """Incluye campos completos para detectar cambios aun sin variar conteos."""
        modelos = (
            MateriaPrima,
            Producto,
            InventarioMateriaPrima,
            InventarioProductoTerminado,
            MovimientoMateriaPrima,
            MovimientoProductoTerminado,
        )
        return {
            modelo._meta.label: list(modelo.objects.order_by('pk').values())
            for modelo in modelos
        }

    def assert_solo_select(self, consultas):
        self.assertGreater(len(consultas), 0)
        for consulta in consultas:
            self.assertTrue(
                consulta['sql'].lstrip().upper().startswith('SELECT'),
                msg=f"CU23 ejecutó una operación distinta de SELECT: {consulta['sql']}",
            )

    @staticmethod
    def indexar(reporte):
        # Los identificadores pertenecen a dos catálogos y pueden coincidir.
        return {
            (fila['tipo'], fila['id']): fila
            for fila in reporte['resultados']
        }


class PruebasServicioReporteExistencias(DatosExistencias, TestCase):
    def test_materia_prima_menor_igual_y_mayor_con_precision_de_milesimas(self):
        filas = self.indexar(reporte_existencias(tipo='materia_prima'))
        casos = (
            (self.harina, '9.999', '10.000', 'bajo_stock'),
            (self.azucar, '10.000', '10.000', 'normal'),
            (self.sal, '10.001', '10.000', 'normal'),
            (self.levadura, '0.001', '0.002', 'bajo_stock'),
        )
        for materia, stock, minimo, estado in casos:
            with self.subTest(materia=materia.nombre):
                fila = filas[('materia_prima', materia.pk)]
                self.assertEqual(fila['stock_actual'], Decimal(stock))
                self.assertEqual(fila['stock_minimo'], Decimal(minimo))
                self.assertEqual(fila['estado'], estado)
                self.assertEqual(fila['origen_minimo'], 'catalogo')

    def test_producto_terminado_19_20_y_21_con_minimo_referencial(self):
        reporte = reporte_existencias(tipo='producto_terminado')
        self.assertEqual(reporte['umbral_productos_terminados'], Decimal('20.000'))
        filas = self.indexar(reporte)
        for producto, stock, estado in (
            (self.pan_integral, '19.000', 'bajo_stock'),
            (self.pan_blanco, '20.000', 'normal'),
            (self.pan_harina, '21.000', 'normal'),
        ):
            with self.subTest(producto=producto.nombre):
                fila = filas[('producto_terminado', producto.pk)]
                self.assertEqual(fila['stock_actual'], Decimal(stock))
                self.assertEqual(fila['stock_minimo'], Decimal('20.000'))
                self.assertEqual(fila['origen_minimo'], 'referencial_global')
                self.assertEqual(fila['unidad_medida'], 'unidades')
                self.assertEqual(fila['estado'], estado)

    def test_cero_con_minimo_cero_es_normal_y_conserva_unidad_de_catalogo(self):
        fila = self.indexar(reporte_existencias())[('materia_prima', self.agua.pk)]
        self.assertEqual(fila['stock_actual'], Decimal('0.000'))
        self.assertEqual(fila['stock_minimo'], Decimal('0.000'))
        self.assertEqual(fila['estado'], 'normal')
        self.assertEqual(fila['unidad_medida'], 'litros')

    def test_incluye_inactivos_con_existencias_en_ambos_catalogos(self):
        filas = self.indexar(reporte_existencias())
        for tipo, articulo, cantidad in (
            ('materia_prima', self.avena, '2.000'),
            ('producto_terminado', self.pan_inactivo, '5.000'),
        ):
            with self.subTest(tipo=tipo):
                fila = filas[(tipo, articulo.pk)]
                self.assertFalse(fila['activo'])
                self.assertEqual(fila['stock_actual'], Decimal(cantidad))
                self.assertEqual(fila['estado'], 'bajo_stock')

    def test_catalogos_sin_inventario_informan_null_y_no_crean_filas(self):
        antes = self.snapshot_inventario()
        reporte = reporte_existencias(estado='sin_inventario')
        self.assertEqual(
            {(fila['tipo'], fila['id']) for fila in reporte['resultados']},
            {('materia_prima', self.manteca.pk), ('producto_terminado', self.cunape.pk)},
        )
        for fila in reporte['resultados']:
            self.assertIsNone(fila['stock_actual'])
            self.assertEqual(fila['estado'], 'sin_inventario')
        self.assertEqual(self.snapshot_inventario(), antes)

    def test_filtro_tipo_y_resumen_corresponden_a_las_filas_filtradas(self):
        for tipo, total, materias, productos, bajos in (
            ('todos', 12, 7, 5, 5),
            ('materia_prima', 7, 7, 0, 3),
            ('producto_terminado', 5, 0, 5, 2),
        ):
            with self.subTest(tipo=tipo):
                reporte = reporte_existencias(tipo=tipo)
                self.assertEqual(reporte['resumen'], {
                    'total': total,
                    'materias_primas': materias,
                    'productos_terminados': productos,
                    'bajo_stock': bajos,
                    'sin_inventario': 2 if tipo == 'todos' else 1,
                })
                self.assertEqual(len(reporte['resultados']), total)
                if tipo != 'todos':
                    self.assertTrue(all(fila['tipo'] == tipo for fila in reporte['resultados']))

    def test_filtro_estado_no_confunde_bajo_stock_y_falta_de_inventario(self):
        for estado, total, materias, productos in (
            ('normal', 5, 3, 2),
            ('bajo_stock', 5, 3, 2),
            ('sin_inventario', 2, 1, 1),
        ):
            with self.subTest(estado=estado):
                reporte = reporte_existencias(estado=estado)
                self.assertEqual(reporte['resumen'], {
                    'total': total,
                    'materias_primas': materias,
                    'productos_terminados': productos,
                    'bajo_stock': total if estado == 'bajo_stock' else 0,
                    'sin_inventario': total if estado == 'sin_inventario' else 0,
                })
                self.assertEqual(len(reporte['resultados']), total)
                self.assertTrue(all(fila['estado'] == estado for fila in reporte['resultados']))

    def test_busqueda_recorta_espacios_y_busca_nombre_en_ambos_catalogos(self):
        reporte = reporte_existencias(q='  HARINA  ')
        self.assertEqual(
            [(fila['tipo'], fila['id']) for fila in reporte['resultados']],
            [('materia_prima', self.harina.pk), ('producto_terminado', self.pan_harina.pk)],
        )
        self.assertEqual(reporte['resumen'], {
            'total': 2, 'materias_primas': 1, 'productos_terminados': 1,
            'bajo_stock': 1, 'sin_inventario': 0,
        })

    def test_filtros_combinados_calculan_resumen_del_resultado_final(self):
        reporte = reporte_existencias(tipo='producto_terminado', q='harina', estado='normal')
        self.assertEqual([fila['id'] for fila in reporte['resultados']], [self.pan_harina.pk])
        self.assertEqual(reporte['resumen'], {
            'total': 1, 'materias_primas': 0, 'productos_terminados': 1,
            'bajo_stock': 0, 'sin_inventario': 0,
        })

    def test_busqueda_sin_coincidencias_devuelve_lista_vacia_y_ceros(self):
        reporte = reporte_existencias(q='catalogo inexistente')
        self.assertEqual(reporte['resultados'], [])
        self.assertEqual(reporte['resumen'], RESUMEN_VACIO)

    def test_orden_tipo_nombre_e_id_desempata_nombres_duplicados(self):
        mp_uno = self.crear_materia('ZZ Duplicado', '1.000')
        mp_dos = self.crear_materia('ZZ Duplicado', '1.000')
        pt_uno = self.crear_producto('ZZ Duplicado', 1)
        pt_dos = self.crear_producto('ZZ Duplicado', 1)
        reporte = reporte_existencias()
        esperado = [
            ('materia_prima', articulo.pk)
            for articulo in (
                self.agua, self.avena, self.azucar, self.harina, self.levadura,
                self.manteca, self.sal, mp_uno, mp_dos,
            )
        ] + [
            ('producto_terminado', articulo.pk)
            for articulo in (
                self.cunape, self.pan_blanco, self.pan_inactivo,
                self.pan_harina, self.pan_integral, pt_uno, pt_dos,
            )
        ]
        self.assertEqual(
            [(fila['tipo'], fila['id']) for fila in reporte['resultados']],
            esperado,
        )

    def test_consultas_acotadas_a_dos_select_sin_mutar_catalogos_ni_movimientos(self):
        antes = self.snapshot_inventario()
        with CaptureQueriesContext(connection) as consultas:
            reporte = reporte_existencias()
        self.assertEqual(len(reporte['resultados']), 12)
        self.assertLessEqual(len(consultas), 2)
        self.assert_solo_select(consultas)
        self.assertEqual(self.snapshot_inventario(), antes)

        # El límite se mantiene al crecer ambos catálogos; evita consultas N+1.
        for indice in range(10):
            self.crear_materia(f'Insumo adicional {indice}', '1.000')
            self.crear_producto(f'Pan adicional {indice}', 30)
        antes_ampliado = self.snapshot_inventario()
        with CaptureQueriesContext(connection) as consultas_ampliadas:
            reporte_ampliado = reporte_existencias()
        self.assertEqual(len(reporte_ampliado['resultados']), 32)
        self.assertLessEqual(len(consultas_ampliadas), 2)
        self.assert_solo_select(consultas_ampliadas)
        self.assertEqual(self.snapshot_inventario(), antes_ampliado)

    def test_igualdad_es_normal_en_cu23_y_conserva_alerta_cu09(self):
        fila = self.indexar(reporte_existencias())[('materia_prima', self.azucar.pk)]
        self.assertEqual(fila['estado'], 'normal')
        self.assertIn(
            self.azucar.pk,
            obtener_materias_primas_bajo_stock().values_list('pk', flat=True),
        )

    def test_veinte_es_normal_en_cu23_y_conserva_critico_cu12(self):
        fila = self.indexar(reporte_existencias())[('producto_terminado', self.pan_blanco.pk)]
        self.assertEqual(fila['estado'], 'normal')
        inventario = InventarioProductoTerminado.objects.select_related('id_producto').get(
            id_producto=self.pan_blanco,
        )
        self.assertEqual(
            InventarioProductoTerminadoSerializer(inventario).data['estado_stock'],
            'critico',
        )


class PruebasReporteExistenciasVacio(TestCase):
    def test_catalogos_vacios_devuelven_umbral_lista_vacia_y_resumen_cero(self):
        cache.clear()
        self.assertFalse(MateriaPrima.objects.exists())
        self.assertFalse(Producto.objects.exists())
        reporte = reporte_existencias()
        self.assertEqual(reporte['umbral_productos_terminados'], Decimal('20.000'))
        self.assertEqual(reporte['resultados'], [])
        self.assertEqual(reporte['resumen'], RESUMEN_VACIO)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasApiReporteExistencias(DatosExistencias, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.permiso = Permiso.objects.create(
            nombre='generar_reportes',
            descripcion='Generar reportes',
            modulo=ModuloPermiso.REPORTES,
        )
        cls.rol_propietario = Rol.objects.create(nombre='Propietario')
        cls.rol_personalizado = Rol.objects.create(nombre='Analista de existencias')
        for rol in (cls.rol_propietario, cls.rol_personalizado):
            RolPermiso.objects.create(rol=rol, permiso=cls.permiso)
        cls.propietario = cls.crear_usuario('propietario_cu23', cls.rol_propietario)
        cls.analista = cls.crear_usuario('analista_cu23', cls.rol_personalizado)
        cls.sin_permiso = []
        for indice, nombre in enumerate((
            'Administrador', 'Personal de Ventas', 'Personal de Producción',
        )):
            rol = Rol.objects.create(nombre=nombre)
            cls.sin_permiso.append(cls.crear_usuario(f'sin_reportes_{indice}', rol))

    @staticmethod
    def crear_usuario(nombre, rol):
        return Usuario.objects.create_user(
            nombre_usuario=nombre,
            password='PanADERIA2026!',
            nombre_completo=nombre,
            email=f'{nombre}@cu23.example.com',
            id_rol=rol,
        )

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = reverse('reportes:reporte-existencias')

    def autenticar(self, usuario=None):
        # Se recorre JWTAuthentication real, sin force_authenticate ni RefreshToken.
        token = AccessToken.for_user(usuario or self.propietario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_propietario_con_jwt_recibe_contrato_completo_y_decimales_en_cadenas(self):
        self.autenticar()
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(set(datos), {'umbral_productos_terminados', 'resumen', 'resultados'})
        self.assertEqual(datos['umbral_productos_terminados'], '20.000')
        self.assertEqual(datos['resumen'], {
            'total': 12, 'materias_primas': 7, 'productos_terminados': 5,
            'bajo_stock': 5, 'sin_inventario': 2,
        })
        filas = self.indexar(datos)
        self.assertEqual(filas[('materia_prima', self.harina.pk)], {
            'id': self.harina.pk,
            'nombre': 'Harina',
            'tipo': 'materia_prima',
            'stock_actual': '9.999',
            'stock_minimo': '10.000',
            'origen_minimo': 'catalogo',
            'unidad_medida': 'kg',
            'estado': 'bajo_stock',
            'activo': True,
        })
        self.assertEqual(filas[('producto_terminado', self.pan_blanco.pk)], {
            'id': self.pan_blanco.pk,
            'nombre': 'Pan blanco',
            'tipo': 'producto_terminado',
            'stock_actual': '20.000',
            'stock_minimo': '20.000',
            'origen_minimo': 'referencial_global',
            'unidad_medida': 'unidades',
            'estado': 'normal',
            'activo': True,
        })
        for tipo, articulo in (
            ('materia_prima', self.manteca), ('producto_terminado', self.cunape),
        ):
            self.assertIsNone(filas[(tipo, articulo.pk)]['stock_actual'])
            self.assertEqual(filas[(tipo, articulo.pk)]['estado'], 'sin_inventario')
        for fila in datos['resultados']:
            self.assertIsInstance(fila['id'], int)
            self.assertIsInstance(fila['activo'], bool)
            self.assertRegex(fila['stock_minimo'], r'^\d+\.\d{3}$')
            if fila['stock_actual'] is not None:
                self.assertRegex(fila['stock_actual'], r'^\d+\.\d{3}$')

    def test_sin_jwt_responde_401(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_invalido_responde_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token-invalido')
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tres_roles_del_sistema_sin_permiso_responden_403(self):
        for usuario in self.sin_permiso:
            with self.subTest(rol=usuario.rol_nombre):
                self.autenticar(usuario)
                self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_rol_personalizado_autorizado_accede_y_revocacion_es_inmediata(self):
        self.autenticar(self.analista)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)
        RolPermiso.objects.filter(rol=self.rol_personalizado, permiso=self.permiso).delete()
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)
        RolPermiso.objects.create(rol=self.rol_personalizado, permiso=self.permiso)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_nombre_propietario_sin_permiso_no_otorga_acceso(self):
        RolPermiso.objects.filter(rol=self.rol_propietario, permiso=self.permiso).delete()
        self.autenticar()
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_filtros_tipo_validos_se_aplican_en_la_api(self):
        self.autenticar()
        for tipo, cantidad in (('todos', 12), ('materia_prima', 7), ('producto_terminado', 5)):
            with self.subTest(tipo=tipo):
                respuesta = self.client.get(self.url, {'tipo': tipo})
                self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
                self.assertEqual(respuesta.data['resumen']['total'], cantidad)
                self.assertEqual(len(respuesta.data['resultados']), cantidad)
                if tipo != 'todos':
                    self.assertTrue(all(fila['tipo'] == tipo for fila in respuesta.data['resultados']))

    def test_filtros_estado_validos_se_aplican_en_la_api(self):
        self.autenticar()
        for estado, cantidad in (
            ('todos', 12), ('normal', 5), ('bajo_stock', 5), ('sin_inventario', 2),
        ):
            with self.subTest(estado=estado):
                respuesta = self.client.get(self.url, {'estado': estado})
                self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
                self.assertEqual(respuesta.data['resumen']['total'], cantidad)
                self.assertEqual(len(respuesta.data['resultados']), cantidad)
                if estado != 'todos':
                    self.assertTrue(all(fila['estado'] == estado for fila in respuesta.data['resultados']))

    def test_busqueda_q_acepta_espacios_y_mayusculas(self):
        self.autenticar()
        respuesta = self.client.get(self.url, {'q': '  HARINA  '})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [fila['nombre'] for fila in respuesta.data['resultados']],
            ['Harina', 'Pan de harina'],
        )
        respuesta_blanca = self.client.get(self.url, {'q': '   '})
        self.assertEqual(respuesta_blanca.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_blanca.data['resumen']['total'], 12)

    def test_q_de_cien_caracteres_es_valida_despues_de_recortar_espacios(self):
        nombre = 'a' * 100
        materia = self.crear_materia(nombre, '1.000')
        self.autenticar()
        respuesta = self.client.get(self.url, {'q': f'  {nombre}  '})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual([fila['id'] for fila in respuesta.data['resultados']], [materia.pk])

    def test_busqueda_por_nombre_no_coincide_con_descripcion_del_producto(self):
        Producto.objects.filter(pk=self.pan_blanco.pk).update(descripcion='Solo descripcion especial')
        self.autenticar()
        respuesta = self.client.get(self.url, {'q': 'descripcion especial'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['resultados'], [])

    def test_filtros_combinados_y_resumen_filtrado_en_la_api(self):
        self.autenticar()
        respuesta = self.client.get(self.url, {
            'tipo': 'materia_prima', 'q': '  harina ', 'estado': 'bajo_stock',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual([fila['id'] for fila in respuesta.data['resultados']], [self.harina.pk])
        self.assertEqual(respuesta.data['resumen'], {
            'total': 1, 'materias_primas': 1, 'productos_terminados': 0,
            'bajo_stock': 1, 'sin_inventario': 0,
        })

    def test_filtros_invalidos_y_q_mayor_de_cien_responden_400(self):
        self.autenticar()
        for campo, valor in (
            ('tipo', 'pan'), ('tipo', ''),
            ('estado', 'critico'), ('estado', ''),
            ('q', 'a' * 101),
        ):
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.client.get(self.url, {campo: valor})
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, respuesta.data)

    def test_busqueda_vacia_devuelve_200_con_resumen_cero(self):
        self.autenticar()
        respuesta = self.client.get(self.url, {'q': 'ninguna coincidencia'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['resultados'], [])
        self.assertEqual(respuesta.data['resumen'], RESUMEN_VACIO)

    def test_get_autenticado_solo_ejecuta_select_y_no_modifica_datos(self):
        self.autenticar()
        antes = self.snapshot_inventario()
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(self.url)
            respuesta_filtrada = self.client.get(self.url, {'estado': 'sin_inventario'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_filtrada.status_code, status.HTTP_200_OK)
        self.assert_solo_select(consultas)
        self.assertEqual(self.snapshot_inventario(), antes)

    def test_post_put_patch_y_delete_responden_405_sin_mutaciones(self):
        self.autenticar()
        antes = self.snapshot_inventario()
        with CaptureQueriesContext(connection) as consultas:
            for metodo in ('post', 'put', 'patch', 'delete'):
                with self.subTest(metodo=metodo):
                    respuesta = getattr(self.client, metodo)(
                        self.url, {'stock_actual': '999.000'}, format='json',
                    )
                    self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assert_solo_select(consultas)
        self.assertEqual(self.snapshot_inventario(), antes)
