"""
Pruebas del CU7 — Registrar compra de materia prima.

Cada clase responde una pregunta de defensa:
    PruebasRegistroCompra   ¿el POST crea compra, stock, precio, movimiento y bitácora?
    PruebasAccesoCompra     ¿quién puede llamar a /api/compras/?
    PruebasDatosInvalidos   ¿qué rechaza el API antes de tocar el inventario?
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.compras.proveedores.models import Proveedor
from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
    TipoMovimientoMateriaPrima,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BasePruebaCU7(TestCase):
    def setUp(self):
        self.client = APIClient()

        permiso = Permiso.objects.create(
            nombre='registrar_compras',
            descripcion='Registrar compras a proveedores',
            modulo=ModuloPermiso.COMPRAS,
        )
        rol = Rol.objects.create(nombre='Propietario', descripcion='Dueño')
        RolPermiso.objects.create(rol=rol, permiso=permiso)

        rol_ventas = Rol.objects.create(nombre='Personal de Ventas', descripcion='Mostrador')

        self.propietario = Usuario.objects.create_user(
            nombre_usuario='csantiago',
            password='PanADERIA2026!',
            nombre_completo='Carlos Santiago',
            email='csantiago.prueba@mail.com',
            id_rol=rol,
        )
        self.vendedor = Usuario.objects.create_user(
            nombre_usuario='ventas',
            password='PanADERIA2026!',
            nombre_completo='Personal de Ventas',
            email='ventas.prueba@mail.com',
            id_rol=rol_ventas,
        )

        self.proveedor = Proveedor.objects.create(nombre='Molinos del Oriente', activo=True)
        self.harina = MateriaPrima.objects.create(
            nombre='Harina',
            unidad_medida='kg',
            stock_minimo=Decimal('20'),
            activo=True,
        )
        self.inventario = InventarioMateriaPrima.objects.create(
            id_materia_prima=self.harina,
            stock_actual=Decimal('0'),
        )

    def _payload(self, **cambios):
        datos = {
            'id_proveedor': self.proveedor.id_proveedor,
            'detalles': [
                {
                    'id_materia_prima': self.harina.id_materia_prima,
                    'cantidad': '10.000',
                    'precio_unitario': '4.50',
                }
            ],
        }
        datos.update(cambios)
        return datos


class PruebasRegistroCompra(BasePruebaCU7):
    def test_post_registra_compra_stock_precio_movimiento_y_bitacora(self):
        self.client.force_authenticate(user=self.propietario)

        respuesta = self.client.post('/api/compras/', self._payload(), format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total'], '45.00')
        self.assertEqual(respuesta.data['proveedor_nombre'], 'Molinos del Oriente')
        self.assertEqual(respuesta.data['registrado_por'], 'csantiago')
        self.assertEqual(len(respuesta.data['detalles']), 1)
        self.assertEqual(respuesta.data['detalles'][0]['subtotal'], '45.00')

        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, Decimal('10.000'))
        self.assertEqual(Compra.objects.count(), 1)
        self.assertEqual(DetalleCompra.objects.count(), 1)
        self.assertTrue(
            HistorialPrecioMateriaPrima.objects.filter(
                id_materia_prima=self.harina,
                precio=Decimal('4.50'),
            ).exists()
        )
        self.assertTrue(
            MovimientoMateriaPrima.objects.filter(
                id_compra_id=respuesta.data['id_compra'],
                tipo=TipoMovimientoMateriaPrima.ENTRADA,
                cantidad=Decimal('10.000'),
            ).exists()
        )
        self.assertTrue(
            Bitacora.objects.filter(
                accion=AccionBitacora.ALTA_COMPRA,
                tabla_afectada='compra',
                usuario=self.propietario,
            ).exists()
        )

    def test_get_detalle_devuelve_la_compra(self):
        self.client.force_authenticate(user=self.propietario)
        creada = self.client.post('/api/compras/', self._payload(), format='json')
        detalle = self.client.get(f"/api/compras/{creada.data['id_compra']}/")

        self.assertEqual(detalle.status_code, status.HTTP_200_OK)
        self.assertEqual(detalle.data['detalles'][0]['nombre_materia_prima'], 'Harina')


class PruebasAccesoCompra(BasePruebaCU7):
    def test_sin_token_responde_401(self):
        respuesta = self.client.post('/api/compras/', self._payload(), format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Compra.objects.count(), 0)

    def test_sin_permiso_responde_403(self):
        self.client.force_authenticate(user=self.vendedor)
        respuesta = self.client.post('/api/compras/', self._payload(), format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Compra.objects.count(), 0)


class PruebasDatosInvalidos(BasePruebaCU7):
    def test_body_vacio_responde_400(self):
        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.post('/api/compras/', {}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('id_proveedor', respuesta.data)
        self.assertIn('detalles', respuesta.data)

    def test_proveedor_inactivo_no_mueve_stock(self):
        self.proveedor.activo = False
        self.proveedor.save(update_fields=['activo'])
        self.client.force_authenticate(user=self.propietario)

        respuesta = self.client.post('/api/compras/', self._payload(), format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, Decimal('0'))
        self.assertEqual(Compra.objects.count(), 0)


class PruebasMejorasCU7(BasePruebaCU7):
    def test_variacion_precio_retorna_advertencia_sin_bloquear_y_registra_en_bitacora(self):
        # 1. Precio inicial registrado: 10.00
        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=self.harina,
            precio=Decimal('10.00'),
        )
        self.client.force_authenticate(user=self.propietario)

        # 2. Compra con variación >= 50% (precio 20.00, +100%)
        payload = self._payload(
            detalles=[
                {
                    'id_materia_prima': self.harina.id_materia_prima,
                    'cantidad': '5.000',
                    'precio_unitario': '20.00',
                }
            ]
        )
        respuesta = self.client.post('/api/compras/', payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIn('advertencias', respuesta.data)
        self.assertEqual(len(respuesta.data['advertencias']), 1)
        self.assertIn('Variación inusual en «Harina»', respuesta.data['advertencias'][0])

        # Verificar que quedó registrado en bitácora con la advertencia
        bitacora = Bitacora.objects.filter(
            accion=AccionBitacora.ALTA_COMPRA,
            tabla_afectada='compra',
        ).latest('id_bitacora')
        self.assertIn('[ADVERTENCIA PRECIO:', bitacora.descripcion)

    def test_listado_con_filtros_y_conteo_lineas(self):
        self.client.force_authenticate(user=self.propietario)
        # Crear compra para Molinos del Oriente
        self.client.post('/api/compras/', self._payload(), format='json')

        # Crear segundo proveedor y compra
        otro_proveedor = Proveedor.objects.create(nombre='Distribuidora Central', activo=True)
        payload2 = self._payload(
            id_proveedor=otro_proveedor.id_proveedor,
            detalles=[
                {
                    'id_materia_prima': self.harina.id_materia_prima,
                    'cantidad': '2.000',
                    'precio_unitario': '5.00',
                }
            ],
        )
        self.client.post('/api/compras/', payload2, format='json')

        # Listado general sin filtros
        res_todos = self.client.get('/api/compras/')
        self.assertEqual(res_todos.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_todos.data), 2)
        self.assertEqual(res_todos.data[0]['cantidad_lineas'], 1)

        # Filtro por search 'Central'
        res_search = self.client.get('/api/compras/?search=Central')
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_search.data), 1)
        self.assertEqual(res_search.data[0]['proveedor_nombre'], 'Distribuidora Central')

        # Filtro por id_proveedor
        res_prov = self.client.get(f'/api/compras/?id_proveedor={self.proveedor.id_proveedor}')
        self.assertEqual(res_prov.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_prov.data), 1)
        self.assertEqual(res_prov.data[0]['proveedor_nombre'], 'Molinos del Oriente')
