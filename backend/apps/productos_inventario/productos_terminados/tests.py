"""
Pruebas automatizadas para CU12: Consultar existencias de productos terminados.
Autor: Roberto (Equipo Panadería Santiago).
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.roles.models import Rol
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.productos_inventario.productos.models import CategoriaProducto, Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    TipoMovimientoProductoTerminado,
)

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasExistenciasProductosTerminados(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Crear permisos necesarios
        self.permiso_inventario = Permiso.objects.create(
            id_permiso=6,
            nombre='gestionar_inventario',
            modulo='productos_inventario',
            descripcion='Consultar existencias',
        )
        self.permiso_ventas = Permiso.objects.create(
            id_permiso=3,
            nombre='registrar_ventas',
            modulo='comercializacion',
            descripcion='Ventas mostrador',
        )

        # 2. Crear rol de Ventas
        self.rol_ventas = Rol.objects.create(
            id_rol=3,
            nombre='Personal de Ventas',
            descripcion='Ventas en mostrador',
        )
        self.rol_ventas.asignar_permiso(self.permiso_inventario)
        self.rol_ventas.asignar_permiso(self.permiso_ventas)

        # 3. Rol sin permisos (para prueba de 403)
        self.rol_sin_acceso = Rol.objects.create(
            id_rol=99,
            nombre='Invitado Sin Permiso',
            descripcion='Sin acceso a inventario',
        )

        # 4. Crear usuarios de prueba
        self.usuario_ventas = Usuario.objects.create_user(
            nombre_usuario='roberto_ventas',
            password='Password123!',
            nombre_completo='Roberto Personal de Ventas',
            email='roberto@panaderia.com',
            id_rol=self.rol_ventas,
        )

        self.usuario_sin_permiso = Usuario.objects.create_user(
            nombre_usuario='sin_acceso',
            password='Password123!',
            nombre_completo='Usuario Limitado',
            email='sinacceso@panaderia.com',
            id_rol=self.rol_sin_acceso,
        )

        # 5. Categorías y Productos de panadería
        self.categoria_tradicional = CategoriaProducto.objects.create(
            nombre='Panes Tradicionales',
            descripcion='Panes de consumo diario',
        )
        self.categoria_especial = CategoriaProducto.objects.create(
            nombre='Panes Dulces',
            descripcion='Especialidades dulces',
        )

        # Pan 1: Marraqueta (Stock normal = 100)
        self.marraqueta = Producto.objects.create(
            nombre='Marraqueta Crujiente',
            id_categoria=self.categoria_tradicional,
            costo_produccion=Decimal('0.50'),
            porcentaje_ganancia=Decimal('60.00'),
            precio_venta=Decimal('0.80'),
            activo=True,
        )
        self.inv_marraqueta = InventarioProductoTerminado.objects.create(
            id_producto=self.marraqueta,
            stock_actual=100,
        )

        # Pan 2: Pan de Leche (Stock crítico = 15)
        self.pan_leche = Producto.objects.create(
            nombre='Pan de Leche Suave',
            id_categoria=self.categoria_especial,
            costo_produccion=Decimal('0.80'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('1.20'),
            activo=True,
        )
        self.inv_leche = InventarioProductoTerminado.objects.create(
            id_producto=self.pan_leche,
            stock_actual=15,
        )

        # Pan 3: Pan Galleta (Stock agotado = 0)
        self.pan_galleta = Producto.objects.create(
            nombre='Pan Galleta Seco',
            id_categoria=self.categoria_tradicional,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        self.inv_galleta = InventarioProductoTerminado.objects.create(
            id_producto=self.pan_galleta,
            stock_actual=0,
        )

        # Movimiento de Kardex de prueba
        MovimientoProductoTerminado.objects.create(
            id_inventario=self.inv_marraqueta,
            tipo=TipoMovimientoProductoTerminado.ENTRADA,
            cantidad=100,
        )

    def test_01_existencias_sin_autenticacion_devuelve_401(self):
        """Un usuario no autenticado debe ser rechazado con 401."""
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_existencias_usuario_sin_permiso_devuelve_403(self):
        """Un usuario autenticado sin el permiso requerido debe recibir 403 Forbidden."""
        self.client.force_authenticate(user=self.usuario_sin_permiso)
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_03_existencias_usuario_autorizado_devuelve_200_con_lista(self):
        """El Personal de Ventas con permiso gestionar_inventario debe consultar existencias exitosamente."""
        self.client.force_authenticate(user=self.usuario_ventas)
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)
        self.assertEqual(len(respuesta.data), 3)

    def test_04_campos_calculados_valor_total_y_estado_stock(self):
        """Verifica que cada ítem incluya valor_total_stock y estado_stock calculados."""
        self.client.force_authenticate(user=self.usuario_ventas)
        respuesta = self.client.get('/api/productos-terminados/existencias/')
        items_por_nombre = {item['producto_nombre']: item for item in respuesta.data}

        # Marraqueta: 100 un * 0.80 = 80.00 Bs, disponible
        marraqueta = items_por_nombre['Marraqueta Crujiente']
        self.assertEqual(marraqueta['stock_actual'], 100)
        self.assertEqual(marraqueta['valor_total_stock'], '80.00')
        self.assertEqual(marraqueta['estado_stock'], 'disponible')

        # Pan de Leche: 15 un * 1.20 = 18.00 Bs, critico
        leche = items_por_nombre['Pan de Leche Suave']
        self.assertEqual(leche['stock_actual'], 15)
        self.assertEqual(leche['valor_total_stock'], '18.00')
        self.assertEqual(leche['estado_stock'], 'critico')

        # Pan Galleta: 0 un, agotado
        galleta = items_por_nombre['Pan Galleta Seco']
        self.assertEqual(galleta['stock_actual'], 0)
        self.assertEqual(galleta['valor_total_stock'], '0.00')
        self.assertEqual(galleta['estado_stock'], 'agotado')

    def test_05_filtro_por_busqueda_q(self):
        """Filtro ?q=Marraqueta retorna únicamente coincidencias del término."""
        self.client.force_authenticate(user=self.usuario_ventas)
        respuesta = self.client.get('/api/productos-terminados/existencias/?q=Marraqueta')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(respuesta.data[0]['producto_nombre'], 'Marraqueta Crujiente')

    def test_06_filtro_por_categoria(self):
        """Filtro ?categoria=<id> filtra por la categoría seleccionada."""
        self.client.force_authenticate(user=self.usuario_ventas)
        respuesta = self.client.get(
            f'/api/productos-terminados/existencias/?categoria={self.categoria_especial.id_categoria}'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(respuesta.data[0]['producto_nombre'], 'Pan de Leche Suave')

    def test_07_filtro_por_estado_stock(self):
        """Filtros ?estado_stock=agotado y ?estado_stock=critico."""
        self.client.force_authenticate(user=self.usuario_ventas)

        # Probar agotado
        resp_agotados = self.client.get('/api/productos-terminados/existencias/?estado_stock=agotado')
        self.assertEqual(len(resp_agotados.data), 1)
        self.assertEqual(resp_agotados.data[0]['producto_nombre'], 'Pan Galleta Seco')

        # Probar critico
        resp_criticos = self.client.get('/api/productos-terminados/existencias/?estado_stock=critico')
        self.assertEqual(len(resp_criticos.data), 1)
        self.assertEqual(resp_criticos.data[0]['producto_nombre'], 'Pan de Leche Suave')

    def test_08_resumen_existencias_kpis(self):
        """El endpoint /resumen/ debe calcular métricas globales acumuladas."""
        self.client.force_authenticate(user=self.usuario_ventas)
        respuesta = self.client.get('/api/productos-terminados/existencias/resumen/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        datos = respuesta.data
        self.assertEqual(datos['total_panes_distintos'], 3)
        self.assertEqual(datos['total_unidades_stock'], 115)  # 100 + 15 + 0
        self.assertEqual(datos['valor_total_inventario'], '98.00')  # 80.00 + 18.00 + 0.00
        self.assertEqual(datos['productos_agotados'], 1)
        self.assertEqual(datos['productos_stock_critico'], 1)
        self.assertEqual(datos['productos_disponibles'], 1)

    def test_09_kardex_movimientos_producto(self):
        """El endpoint /<id>/movimientos/ debe retornar el historial de entradas/salidas."""
        self.client.force_authenticate(user=self.usuario_ventas)
        url = f'/api/productos-terminados/existencias/{self.marraqueta.id_producto}/movimientos/'
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        self.assertEqual(respuesta.data['producto_nombre'], 'Marraqueta Crujiente')
        self.assertEqual(respuesta.data['stock_actual'], 100)
        self.assertEqual(len(respuesta.data['movimientos']), 1)
        self.assertEqual(respuesta.data['movimientos'][0]['tipo'], 'entrada')
        self.assertEqual(respuesta.data['movimientos'][0]['cantidad'], 100)
