"""
Pruebas automatizadas de la sub-app de Producción.
Casos de Uso:
  - CU10: Registrar producción diaria (simulación, explosión BOM, validación de stock,
          transacción atómica, kardex de insumos y producto terminado, bitácora).
  - CU11: Consultar historial de producción (filtros, permisos RBAC, detalle).
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
)
from apps.productos_inventario.produccion.models import (
    DetalleProduccion,
    JornadaProduccion,
    Produccion,
)
from apps.productos_inventario.productos.models import (
    CategoriaProducto,
    Producto,
    ProductoMateriaPrima,
)
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasBaseProduccion(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Configuración de Roles y Permisos
        self.rol_produccion = Rol.objects.create(
            nombre='Personal de Producción',
            descripcion='Registro de producción diaria y consulta del historial',
        )
        self.permiso_produccion = Permiso.objects.create(
            nombre='registrar_produccion',
            modulo='productos_inventario',
            descripcion='Registrar cantidades producidas por jornada',
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
            descripcion='No tiene permisos para producción',
        )
        self.usuario_sin_permiso = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password='PanADERIA2026!',
            nombre_completo='Ana Vendedor',
            email='vendedor.prueba@mail.com',
            id_rol=self.rol_sin_permiso,
        )

        # 2. Catálogo de prueba para CU10
        self.categoria = CategoriaProducto.objects.create(
            nombre='Tradicionales',
            descripcion='Panes de consumo diario',
        )
        self.producto_marraqueta = Producto.objects.create(
            nombre='Marraqueta',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        self.producto_casero = Producto.objects.create(
            nombre='Casero',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.45'),
            porcentaje_ganancia=Decimal('55.00'),
            precio_venta=Decimal('0.70'),
            activo=True,
        )

        # 3. Materias Primas con inventario inicial y precios de compra
        self.mp_harina = MateriaPrima.objects.create(
            nombre='Harina',
            unidad_medida='kg',
            stock_minimo=Decimal('20.000'),
            activo=True,
        )
        self.inv_harina = InventarioMateriaPrima.objects.create(
            id_materia_prima=self.mp_harina,
            stock_actual=Decimal('100.000'),
        )
        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=self.mp_harina,
            precio=Decimal('4.50'),
        )

        self.mp_levadura = MateriaPrima.objects.create(
            nombre='Levadura',
            unidad_medida='kg',
            stock_minimo=Decimal('2.000'),
            activo=True,
        )
        self.inv_levadura = InventarioMateriaPrima.objects.create(
            id_materia_prima=self.mp_levadura,
            stock_actual=Decimal('10.000'),
        )
        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=self.mp_levadura,
            precio=Decimal('45.00'),
        )

        self.mp_sal = MateriaPrima.objects.create(
            nombre='Sal',
            unidad_medida='kg',
            stock_minimo=Decimal('3.000'),
            activo=True,
        )
        self.inv_sal = InventarioMateriaPrima.objects.create(
            id_materia_prima=self.mp_sal,
            stock_actual=Decimal('15.000'),
        )
        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=self.mp_sal,
            precio=Decimal('3.00'),
        )

        # 4. Recetas (BOM): 1 Marraqueta = 0.060 kg Harina + 0.002 kg Levadura + 0.001 kg Sal
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_marraqueta,
            id_materia_prima=self.mp_harina,
            cantidad_requerida=Decimal('0.060'),
            unidad_medida='kg',
        )
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_marraqueta,
            id_materia_prima=self.mp_levadura,
            cantidad_requerida=Decimal('0.002'),
            unidad_medida='kg',
        )
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_marraqueta,
            id_materia_prima=self.mp_sal,
            cantidad_requerida=Decimal('0.001'),
            unidad_medida='kg',
        )

        # Receta Casero: 0.070 kg Harina + 0.002 kg Levadura + 0.001 kg Sal
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_casero,
            id_materia_prima=self.mp_harina,
            cantidad_requerida=Decimal('0.070'),
            unidad_medida='kg',
        )
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_casero,
            id_materia_prima=self.mp_levadura,
            cantidad_requerida=Decimal('0.002'),
            unidad_medida='kg',
        )
        ProductoMateriaPrima.objects.create(
            id_producto=self.producto_casero,
            id_materia_prima=self.mp_sal,
            cantidad_requerida=Decimal('0.001'),
            unidad_medida='kg',
        )

    # =========================================================================
    # PRUEBAS CU11 — CONSULTAR HISTORIAL DE PRODUCCIÓN
    # =========================================================================

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
            descripcion='Gestión de catálogo y productos',
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

    # =========================================================================
    # PRUEBAS CU10 — REGISTRAR PRODUCCIÓN DIARIA & SIMULACIÓN
    # =========================================================================

    def test_simulacion_consumo_insumos_viable(self):
        """Simula 200 Marraquetas y 100 Caseros, verificando la explosión de materiales."""
        self.client.force_authenticate(user=self.usuario)
        payload = {
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 200},
                {'id_producto': self.producto_casero.id_producto, 'cantidad_producida': 100},
            ]
        }
        respuesta = self.client.post('/api/produccion/simular/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.data
        self.assertTrue(datos['es_viable'])
        self.assertEqual(datos['total_panes_unidades'], 300)

        # 200 * 0.060 + 100 * 0.070 = 12.0 + 7.0 = 19.0 kg Harina
        insumo_harina = next(i for i in datos['insumos'] if i['nombre_insumo'] == 'Harina')
        self.assertAlmostEqual(insumo_harina['cantidad_requerida'], 19.0, places=3)
        self.assertTrue(insumo_harina['suficiente'])

    def test_simulacion_consumo_insumos_no_viable_por_falta_de_stock(self):
        """Simula una cantidad desmedida (5000 panes) que excede el stock actual de harina."""
        self.client.force_authenticate(user=self.usuario)
        payload = {
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 5000},
            ]
        }
        respuesta = self.client.post('/api/produccion/simular/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.data
        self.assertFalse(datos['es_viable'])
        insumo_harina = next(i for i in datos['insumos'] if i['nombre_insumo'] == 'Harina')
        self.assertFalse(insumo_harina['suficiente'])
        self.assertGreater(insumo_harina['diferencia_faltante'], 0)

    def test_registro_produccion_camino_feliz_transaccional(self):
        """
        Registra 100 Marraquetas y 50 Caseros:
          - Descuenta 9.5 kg de harina (100*0.06 + 50*0.07), levadura y sal.
          - Suma 100 y 50 al inventario de producto terminado.
          - Genera kardex de entrada y salida con id_produccion.
          - Registra evento en Bitácora (CU26).
        """
        self.client.force_authenticate(user=self.usuario)
        payload = {
            'fecha': '2026-10-13',
            'jornada': 'Mañana',
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 100},
                {'id_producto': self.producto_casero.id_producto, 'cantidad_producida': 50},
            ]
        }

        respuesta = self.client.post('/api/produccion/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total_unidades'], 150)
        self.assertEqual(respuesta.data['total_variedades'], 2)

        id_produccion = respuesta.data['id_produccion']
        produccion_db = Produccion.objects.get(id_produccion=id_produccion)
        self.assertEqual(str(produccion_db.fecha), '2026-10-13')
        self.assertEqual(produccion_db.jornada, 'Mañana')
        self.assertEqual(produccion_db.detalles.count(), 2)

        # 1. Verificar inventario de materia prima descontado
        # Harina consumida: 100 * 0.060 + 50 * 0.070 = 6.0 + 3.5 = 9.5 kg -> Quedan 90.5 kg
        self.inv_harina.refresh_from_db()
        self.assertEqual(self.inv_harina.stock_actual, Decimal('90.500'))

        # Levadura consumida: 100 * 0.002 + 50 * 0.002 = 0.3 kg -> Quedan 9.7 kg
        self.inv_levadura.refresh_from_db()
        self.assertEqual(self.inv_levadura.stock_actual, Decimal('9.700'))

        # Sal consumida: 100 * 0.001 + 50 * 0.001 = 0.15 kg -> Quedan 14.85 kg
        self.inv_sal.refresh_from_db()
        self.assertEqual(self.inv_sal.stock_actual, Decimal('14.850'))

        # 2. Verificar movimientos de salida en materia prima (Kardex MP)
        movs_mp = MovimientoMateriaPrima.objects.filter(id_produccion=produccion_db)
        self.assertEqual(movs_mp.count(), 3)
        self.assertTrue(all(m.tipo == 'salida' for m in movs_mp))

        # 3. Verificar inventario de producto terminado incrementado
        inv_pt_marraqueta = InventarioProductoTerminado.objects.get(id_producto=self.producto_marraqueta)
        self.assertEqual(inv_pt_marraqueta.stock_actual, 100)
        inv_pt_casero = InventarioProductoTerminado.objects.get(id_producto=self.producto_casero)
        self.assertEqual(inv_pt_casero.stock_actual, 50)

        # 4. Verificar movimientos de entrada en producto terminado (Kardex PT)
        movs_pt = MovimientoProductoTerminado.objects.filter(id_produccion=produccion_db)
        self.assertEqual(movs_pt.count(), 2)
        self.assertTrue(all(m.tipo == 'entrada' for m in movs_pt))

        # 5. Verificar bitácora de auditoría (CU26)
        bitacora = Bitacora.objects.filter(accion=AccionBitacora.REGISTRO_PRODUCCION, tabla_afectada='produccion').first()
        self.assertIsNotNone(bitacora)
        self.assertEqual(bitacora.usuario, self.usuario)
        self.assertIn(str(id_produccion), bitacora.descripcion)

    def test_registro_produccion_falla_por_stock_insuficiente_y_revierte_todo(self):
        """Si falta stock de algún ingrediente, la transacción se cancela por completo sin tocar la BD."""
        self.client.force_authenticate(user=self.usuario)
        # 100 kg disponibles de harina. 2000 marraquetas requieren 120 kg de harina.
        payload = {
            'fecha': '2026-10-13',
            'jornada': 'Tarde',
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 2000},
            ]
        }

        respuesta = self.client.post('/api/produccion/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No hay suficiente materia prima', respuesta.data['error'])

        # Comprobar que no se creó registro de Producción
        self.assertEqual(Produccion.objects.count(), 0)
        self.assertEqual(DetalleProduccion.objects.count(), 0)

        # Comprobar que el inventario no se modificó
        self.inv_harina.refresh_from_db()
        self.assertEqual(self.inv_harina.stock_actual, Decimal('100.000'))
        self.assertEqual(InventarioProductoTerminado.objects.count(), 0)

    def test_registro_produccion_sin_detalles_responde_400(self):
        self.client.force_authenticate(user=self.usuario)
        payload = {
            'fecha': '2026-10-13',
            'jornada': 'Mañana',
            'detalles': [],
        }
        respuesta = self.client.post('/api/produccion/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_produccion_cantidades_en_cero_responde_400(self):
        self.client.force_authenticate(user=self.usuario)
        payload = {
            'fecha': '2026-10-13',
            'jornada': 'Mañana',
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 0},
            ],
        }
        respuesta = self.client.post('/api/produccion/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_produccion_usuario_sin_permiso_responde_403(self):
        self.client.force_authenticate(user=self.usuario_sin_permiso)
        payload = {
            'fecha': '2026-10-13',
            'jornada': 'Mañana',
            'detalles': [
                {'id_producto': self.producto_marraqueta.id_producto, 'cantidad_producida': 50},
            ],
        }
        respuesta = self.client.post('/api/produccion/', data=payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_endpoint_recetas_retorna_lista_con_insumos(self):
        self.client.force_authenticate(user=self.usuario)
        respuesta = self.client.get('/api/produccion/recetas/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIsInstance(respuesta.data, list)
        marraqueta = next((p for p in respuesta.data if p['nombre_producto'] == 'Marraqueta'), None)
        self.assertIsNotNone(marraqueta)
        self.assertEqual(len(marraqueta['insumos']), 3)

    def test_seeder_recetas_ejecuta_correctamente(self):
        call_command('seed_productos')
        call_command('seed_materias_primas')
        call_command('seed_recetas')
        recetas_marraqueta = ProductoMateriaPrima.objects.filter(id_producto__nombre='Marraqueta')
        self.assertEqual(recetas_marraqueta.count(), 3)
        self.assertEqual(ProductoMateriaPrima.objects.count(), 37)
