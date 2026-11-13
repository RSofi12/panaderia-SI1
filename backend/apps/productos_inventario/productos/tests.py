from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIClient

from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.productos_inventario.productos.models import (
    CategoriaProducto,
    HistorialPrecioProducto,
    Producto,
)

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasGestionProductos(TestCase):
    def setUp(self):
        self.client = APIClient()

        perm_productos = Permiso.objects.create(
            nombre='gestionar_productos',
            descripcion='Permite gestionar productos',
            modulo=ModuloPermiso.PRODUCTOS_INVENTARIO,
        )
        rol_admin = Rol.objects.create(nombre='Administrador', descripcion='Admin')
        RolPermiso.objects.create(rol=rol_admin, permiso=perm_productos)

        self.usuario_admin = Usuario.objects.create_user(
            nombre_usuario='admin_prod',
            email='admin_prod@panaderia.com',
            nombre_completo='Admin Productos',
            password='Password123!',
            id_rol=rol_admin,
        )

        self.categoria = CategoriaProducto.objects.create(
            nombre='Tradicionales',
            descripcion='Panes tradicionales',
        )

    def test_listar_categorias_y_productos(self):
        self.client.force_authenticate(user=self.usuario_admin)
        Producto.objects.create(
            nombre='Marraqueta',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
        )

        res_cat = self.client.get(reverse('productos_inventario:categorias_producto'))
        self.assertEqual(res_cat.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_cat.data), 1)

        res_prod = self.client.get(reverse('productos_inventario:productos'))
        self.assertEqual(res_prod.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_prod.data), 1)
        self.assertEqual(res_prod.data[0]['nombre'], 'Marraqueta')

    def test_crear_producto_calcula_precio_sugerido_y_registra_historial_y_bitacora(self):
        self.client.force_authenticate(user=self.usuario_admin)
        data = {
            'nombre': 'Pan Casero',
            'id_categoria': self.categoria.id_categoria,
            'costo_produccion': '0.45',
            'porcentaje_ganancia': '55.00',
            'precio_venta': '0.70',
        }
        res = self.client.post(reverse('productos_inventario:productos'), data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        producto = Producto.objects.get(nombre='Pan Casero')
        # precio_sugerido = 0.45 * (1 + 0.55) = 0.6975 -> 0.70
        self.assertEqual(producto.precio_sugerido, Decimal('0.70'))

        # Historial de precio creado
        historial = HistorialPrecioProducto.objects.filter(id_producto=producto)
        self.assertEqual(historial.count(), 1)
        self.assertEqual(historial.first().precio, Decimal('0.70'))

        # Bitácora registrada
        self.assertTrue(
            Bitacora.objects.filter(
                usuario=self.usuario_admin,
                accion=AccionBitacora.ALTA_PRODUCTO,
            ).exists()
        )

    def test_toggle_activo_producto(self):
        self.client.force_authenticate(user=self.usuario_admin)
        prod = Producto.objects.create(
            nombre='Pan Mollete',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        url = reverse('productos_inventario:producto_toggle_activo', kwargs={'pk': prod.pk})
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        prod.refresh_from_db()
        self.assertFalse(prod.activo)

    def test_cambiar_precio_agrega_una_entrada_sin_alterar_la_anterior(self):
        self.client.force_authenticate(user=self.usuario_admin)
        producto = Producto.objects.create(nombre='Pan integral', precio_venta='1.50')
        anterior = HistorialPrecioProducto.objects.create(id_producto=producto, precio='1.50')
        url = reverse('productos_inventario:producto_detalle', kwargs={'pk': producto.pk})

        respuesta = self.client.patch(url, {'precio_venta': '1.75'}, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        anterior.refresh_from_db()
        self.assertEqual(anterior.precio, Decimal('1.50'))
        self.assertEqual(producto.historial_precios.count(), 2)
        self.assertTrue(producto.historial_precios.filter(precio=Decimal('1.75')).exists())

    def test_editar_sin_cambiar_precio_no_duplica_historial(self):
        self.client.force_authenticate(user=self.usuario_admin)
        producto = Producto.objects.create(nombre='Pan integral', precio_venta='1.50')
        HistorialPrecioProducto.objects.create(id_producto=producto, precio='1.50')
        url = reverse('productos_inventario:producto_detalle', kwargs={'pk': producto.pk})

        respuesta = self.client.patch(
            url, {'nombre': 'Pan integral grande', 'precio_venta': '1.50'}, format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(producto.historial_precios.count(), 1)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasHistorialPreciosCU19(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.permiso = Permiso.objects.create(
            nombre='gestionar_productos',
            modulo=ModuloPermiso.PRODUCTOS_INVENTARIO,
        )
        cls.usuarios = {}
        for nombre, codigo in (
            ('Propietario', 'propietario'),
            ('Administrador', 'administrador'),
            ('Personal de Ventas', 'ventas'),
            ('Personal de Producción', 'produccion'),
        ):
            rol = Rol.objects.create(nombre=nombre)
            # Todos reciben el permiso para demostrar que el rol también se exige.
            RolPermiso.objects.create(rol=rol, permiso=cls.permiso)
            cls.usuarios[codigo] = Usuario.objects.create_user(
                nombre_usuario=f'cu19_{codigo}',
                nombre_completo=f'Pruebas CU19 {nombre}',
                email=f'cu19_{codigo}@example.com',
                password='Password123!',
                id_rol=rol,
            )
        cls.propietario = cls.usuarios['propietario']
        cls.producto = Producto.objects.create(nombre='Marraqueta', precio_venta='0.60')
        cls.otro_producto = Producto.objects.create(nombre='Cuñapé', precio_venta='2.50')
        cls.producto_sin_historial = Producto.objects.create(
            nombre='Producto sin historia registrada', precio_venta='9.99'
        )
        cls.fecha = datetime(2026, 10, 22, 16, 30, tzinfo=datetime_timezone.utc)

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.client.force_authenticate(user=self.propietario)
        self.url = reverse('productos_inventario:historial_precios')

    def crear_historial(self, producto=None, precio='0.60', fecha=None):
        return HistorialPrecioProducto.objects.create(
            id_producto=producto or self.producto,
            precio=Decimal(precio),
            fecha_inicio=fecha or self.fecha,
        )

    def ids_resultados(self, respuesta):
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return [fila['id_historial'] for fila in respuesta.data['results']]

    def test_propietario_autorizado_recibe_contrato_de_lectura(self):
        registro = self.crear_historial()

        respuesta = self.client.get(self.url)

        self.assertEqual(self.ids_resultados(respuesta), [registro.pk])
        self.assertEqual(set(respuesta.data), {'count', 'next', 'previous', 'results'})
        fila = respuesta.data['results'][0]
        self.assertEqual(set(fila), {
            'id_historial', 'id_producto', 'producto_nombre',
            'producto_activo', 'precio', 'fecha_inicio',
        })
        self.assertEqual(fila['id_producto'], self.producto.pk)
        self.assertEqual(fila['producto_nombre'], 'Marraqueta')
        self.assertTrue(fila['producto_activo'])
        self.assertEqual(fila['precio'], '0.60')
        self.assertEqual(datetime.fromisoformat(fila['fecha_inicio']), self.fecha)

    def test_ventas_con_permiso_no_puede_consultar(self):
        self.client.force_authenticate(user=self.usuarios['ventas'])
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_produccion_con_permiso_no_puede_consultar(self):
        self.client.force_authenticate(user=self.usuarios['produccion'])
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_con_permiso_no_puede_consultar(self):
        self.client.force_authenticate(user=self.usuarios['administrador'])
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_superusuario_de_otro_rol_no_omite_restriccion(self):
        usuario = self.usuarios['administrador']
        usuario.is_superuser = True
        usuario.save(update_fields=['is_superuser'])
        self.client.force_authenticate(user=usuario)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_usuario_sin_rol_no_puede_consultar(self):
        self.propietario.id_rol = None
        self.propietario.save(update_fields=['id_rol'])
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_autenticacion_responde_401(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_propietario_sin_permiso_no_puede_consultar(self):
        RolPermiso.objects.filter(rol=self.propietario.id_rol, permiso=self.permiso).delete()
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_historial_vacio_no_fabrica_precios_desde_el_catalogo(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, {
            'count': 0, 'next': None, 'previous': None, 'results': [],
        })

    def test_filtra_por_producto(self):
        esperado = self.crear_historial()
        self.crear_historial(producto=self.otro_producto, precio='2.50')

        respuesta = self.client.get(self.url, {'id_producto': self.producto.pk})

        self.assertEqual(self.ids_resultados(respuesta), [esperado.pk])

    def test_producto_sin_historial_y_id_inexistente_dan_resultado_vacio(self):
        self.crear_historial()
        for identificador in (self.producto_sin_historial.pk, 9223372036854775807):
            with self.subTest(id_producto=identificador):
                respuesta = self.client.get(self.url, {'id_producto': identificador})
                self.assertEqual(self.ids_resultados(respuesta), [])
                self.assertEqual(respuesta.data['count'], 0)

    def test_rechaza_identificadores_invalidos_sin_error_de_base_de_datos(self):
        for identificador in ('0', '-1', 'abc', '1.5', '', '9223372036854775808'):
            with self.subTest(id_producto=identificador):
                respuesta = self.client.get(self.url, {'id_producto': identificador})
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('id_producto', respuesta.data)

    def test_fechas_incluyen_dia_completo_de_bolivia(self):
        inicio = datetime(2026, 10, 22, 4, tzinfo=datetime_timezone.utc)
        fin = datetime(2026, 10, 23, 3, 59, 59, 999999, tzinfo=datetime_timezone.utc)
        self.crear_historial(fecha=inicio - timedelta(microseconds=1))
        primero = self.crear_historial(fecha=inicio)
        ultimo = self.crear_historial(fecha=fin)
        self.crear_historial(fecha=fin + timedelta(microseconds=1))

        # La zona activa de una petición no debe cambiar el día de negocio.
        with timezone.override('UTC'):
            respuesta = self.client.get(self.url, {
                'fecha_desde': '2026-10-22', 'fecha_hasta': '2026-10-22',
            })

        self.assertEqual(self.ids_resultados(respuesta), [ultimo.pk, primero.pk])

    def test_filtro_fecha_desde_independiente(self):
        self.crear_historial(fecha=self.fecha - timedelta(days=1))
        esperado = self.crear_historial()
        respuesta = self.client.get(self.url, {'fecha_desde': '2026-10-22'})
        self.assertEqual(self.ids_resultados(respuesta), [esperado.pk])

    def test_filtro_fecha_hasta_independiente(self):
        esperado = self.crear_historial()
        self.crear_historial(fecha=self.fecha + timedelta(days=1))
        respuesta = self.client.get(self.url, {'fecha_hasta': '2026-10-22'})
        self.assertEqual(self.ids_resultados(respuesta), [esperado.pk])

    def test_combina_producto_y_rango_de_fechas(self):
        esperado = self.crear_historial()
        self.crear_historial(producto=self.otro_producto)
        self.crear_historial(fecha=self.fecha - timedelta(days=1))

        respuesta = self.client.get(self.url, {
            'id_producto': self.producto.pk,
            'fecha_desde': '2026-10-22',
            'fecha_hasta': '2026-10-22',
        })

        self.assertEqual(self.ids_resultados(respuesta), [esperado.pk])

    def test_filtros_sin_coincidencias_devuelven_lista_vacia(self):
        self.crear_historial()
        respuesta = self.client.get(self.url, {'fecha_desde': '2026-10-23'})
        self.assertEqual(self.ids_resultados(respuesta), [])

    def test_rechaza_fechas_invalidas(self):
        for campo in ('fecha_desde', 'fecha_hasta'):
            for valor in ('invalida', '2026-02-30', '22/10/2026', ''):
                with self.subTest(campo=campo, valor=valor):
                    respuesta = self.client.get(self.url, {campo: valor})
                    self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn(campo, respuesta.data)

    def test_rechaza_rango_invertido(self):
        respuesta = self.client.get(self.url, {
            'fecha_desde': '2026-10-23', 'fecha_hasta': '2026-10-22',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_hasta', respuesta.data)

    def test_orden_reciente_y_desempate_por_id_descendente(self):
        antiguo = self.crear_historial(fecha=self.fecha - timedelta(days=1))
        primero = self.crear_historial()
        segundo = self.crear_historial()

        respuesta = self.client.get(self.url)

        self.assertEqual(self.ids_resultados(respuesta), [segundo.pk, primero.pk, antiguo.pk])

    def test_paginacion_conserva_filtros_y_no_repite_registros(self):
        registros = [self.crear_historial() for _ in range(12)]
        self.crear_historial(producto=self.otro_producto)

        primera = self.client.get(self.url, {'id_producto': self.producto.pk})
        segunda = self.client.get(self.url, {'id_producto': self.producto.pk, 'page': 2})

        self.assertEqual(primera.data['count'], 12)
        self.assertEqual(len(self.ids_resultados(primera)), 10)
        self.assertEqual(len(self.ids_resultados(segunda)), 2)
        self.assertIsNone(primera.data['previous'])
        self.assertIsNone(segunda.data['next'])
        self.assertIn(f'id_producto={self.producto.pk}', primera.data['next'])
        self.assertIn('page=2', primera.data['next'])
        self.assertIsNotNone(segunda.data['previous'])
        self.assertEqual(
            self.ids_resultados(primera) + self.ids_resultados(segunda),
            [registro.pk for registro in reversed(registros)],
        )

    def test_paginacion_mantiene_diez_filas_si_cambia_el_valor_global(self):
        for _ in range(12):
            self.crear_historial()

        for tamano_global in (3, None):
            with self.subTest(tamano_global=tamano_global):
                with patch.object(PageNumberPagination, 'page_size', tamano_global):
                    primera = self.client.get(self.url)
                    segunda = self.client.get(self.url, {'page': 2})

                self.assertEqual(primera.status_code, status.HTTP_200_OK)
                self.assertEqual(segunda.status_code, status.HTTP_200_OK)
                self.assertEqual(primera.data['count'], 12)
                self.assertEqual(len(primera.data['results']), 10)
                self.assertEqual(len(segunda.data['results']), 2)
                self.assertIsNone(primera.data['previous'])
                self.assertIn('page=2', primera.data['next'])
                self.assertIsNotNone(segunda.data['previous'])
                self.assertIsNone(segunda.data['next'])

    def test_precio_decimal_se_serializa_sin_perdida_de_precision(self):
        for precio in ('0.00', '0.10', '12345678.91', '99999999.99'):
            with self.subTest(precio=precio):
                registro = self.crear_historial(precio=precio)
                respuesta = self.client.get(self.url)
                fila = next(
                    fila for fila in respuesta.data['results']
                    if fila['id_historial'] == registro.pk
                )
                self.assertIsInstance(fila['precio'], str)
                self.assertEqual(fila['precio'], precio)

    def test_incluye_historial_de_producto_inactivo(self):
        self.producto.activo = False
        self.producto.save(update_fields=['activo'])
        registro = self.crear_historial()

        respuesta = self.client.get(self.url, {'id_producto': self.producto.pk})

        self.assertEqual(self.ids_resultados(respuesta), [registro.pk])
        self.assertFalse(respuesta.data['results'][0]['producto_activo'])

    def test_lectura_precarga_productos_sin_consultas_por_fila(self):
        from apps.productos_inventario.productos.selectors import (
            obtener_historial_precios_productos,
        )
        from apps.productos_inventario.productos.serializers import (
            HistorialPrecioProductoSerializer,
        )

        self.crear_historial()
        self.crear_historial(producto=self.otro_producto)
        with self.assertNumQueries(1):
            datos = HistorialPrecioProductoSerializer(
                obtener_historial_precios_productos(), many=True
            ).data
        self.assertEqual(len(datos), 2)

    def test_get_no_modifica_precios_productos_inventarios_ni_compras(self):
        from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
        from apps.compras.proveedores.models import Proveedor
        from apps.productos_inventario.materia_prima.models import (
            HistorialPrecioMateriaPrima,
            InventarioMateriaPrima,
            MateriaPrima,
            MovimientoMateriaPrima,
        )
        from apps.productos_inventario.productos_terminados.models import (
            InventarioProductoTerminado,
            MovimientoProductoTerminado,
        )

        self.crear_historial()
        InventarioProductoTerminado.objects.create(id_producto=self.producto, stock_actual=17)
        materia = MateriaPrima.objects.create(nombre='Harina CU19', unidad_medida='kg')
        InventarioMateriaPrima.objects.create(id_materia_prima=materia, stock_actual='8.125')
        HistorialPrecioMateriaPrima.objects.create(id_materia_prima=materia, precio='12.30')
        proveedor = Proveedor.objects.create(nombre='Proveedor CU19')
        compra = Compra.objects.create(
            id_proveedor=proveedor, id_usuario=self.propietario, total='24.60'
        )
        DetalleCompra.objects.create(
            id_compra=compra, id_materia_prima=materia,
            cantidad='2.000', precio_unitario='12.30', subtotal='24.60',
        )
        modelos = (
            Producto, HistorialPrecioProducto, InventarioProductoTerminado,
            MovimientoProductoTerminado, MateriaPrima, InventarioMateriaPrima,
            HistorialPrecioMateriaPrima, MovimientoMateriaPrima,
            Compra, DetalleCompra, Proveedor, Bitacora,
        )

        def estado_negocio():
            return {
                modelo._meta.label: list(modelo.objects.order_by('pk').values())
                for modelo in modelos
            }

        antes = estado_negocio()
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(self.url, {'id_producto': self.producto.pk})

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(estado_negocio(), antes)
        escrituras = [
            consulta['sql'] for consulta in consultas.captured_queries
            if re.match(
                r'^\s*(INSERT|UPDATE|DELETE|TRUNCATE|ALTER|CREATE|DROP)\b',
                consulta['sql'], flags=re.IGNORECASE,
            )
        ]
        self.assertEqual(escrituras, [])

    def test_metodos_de_escritura_no_disponibles(self):
        registro = self.crear_historial()
        antes = list(HistorialPrecioProducto.objects.values())
        for metodo in ('post', 'put', 'patch', 'delete'):
            with self.subTest(metodo=metodo):
                respuesta = getattr(self.client, metodo)(
                    self.url, {'id_historial': registro.pk, 'precio': '99.99'}, format='json'
                )
                self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(list(HistorialPrecioProducto.objects.values()), antes)

    def test_catalogo_anterior_sigue_sin_paginacion_para_ventas_sin_permiso(self):
        usuario = self.usuarios['ventas']
        RolPermiso.objects.filter(rol=usuario.id_rol, permiso=self.permiso).delete()
        self.client.force_authenticate(user=usuario)

        respuesta = self.client.get(reverse('productos_inventario:productos'))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)
        self.assertEqual(len(respuesta.data), 3)

    def test_rutas_nuevas_y_anteriores_se_resuelven_sin_conflictos(self):
        self.assertEqual(self.url, '/api/productos/historial-precios/')
        for ruta, nombre in (
            (self.url, 'historial_precios'),
            ('/api/productos/', 'productos'),
            ('/api/productos/recetas/', 'productos_recetas'),
            (f'/api/productos/{self.producto.pk}/', 'producto_detalle'),
            (f'/api/productos/{self.producto.pk}/toggle-activo/', 'producto_toggle_activo'),
        ):
            with self.subTest(ruta=ruta):
                self.assertEqual(resolve(ruta).url_name, nombre)
