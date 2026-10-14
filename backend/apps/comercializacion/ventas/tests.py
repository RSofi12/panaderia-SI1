"""
Pruebas del CU13 — Registrar venta en mostrador.

Efectivo guarda la venta con id_transaccion_stripe vacío.
Stripe exige un cobro confirmado y, si no hay stock, no deja la venta escrita.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.comercializacion.ventas.models import DetalleVenta, Venta
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    TipoMovimientoProductoTerminado,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BaseVenta(TestCase):
    def setUp(self):
        self.client = APIClient()
        permiso = Permiso.objects.create(
            nombre='registrar_ventas',
            descripcion='Registrar ventas',
            modulo=ModuloPermiso.COMERCIALIZACION,
        )
        rol_ventas = Rol.objects.create(nombre='Personal de Ventas', descripcion='Mostrador')
        RolPermiso.objects.create(rol=rol_ventas, permiso=permiso)
        rol_produccion = Rol.objects.create(nombre='Personal de Producción', descripcion='Horno')

        self.vendedor = Usuario.objects.create_user(
            nombre_usuario='mgonzales',
            password='PanADERIA2026!',
            nombre_completo='María Gonzales',
            email='ventas.prueba@mail.com',
            id_rol=rol_ventas,
        )
        self.produccion = Usuario.objects.create_user(
            nombre_usuario='mrojas',
            password='PanADERIA2026!',
            nombre_completo='Miguel Rojas',
            email='produccion.prueba@mail.com',
            id_rol=rol_produccion,
        )
        self.marraqueta = Producto.objects.create(
            nombre='Marraqueta',
            precio_venta=Decimal('0.50'),
            activo=True,
        )
        self.arani = Producto.objects.create(
            nombre='Pan Arani',
            precio_venta=Decimal('1.00'),
            activo=True,
        )
        self.stock_marraqueta = InventarioProductoTerminado.objects.create(
            id_producto=self.marraqueta,
            stock_actual=10,
        )
        self.stock_arani = InventarioProductoTerminado.objects.create(
            id_producto=self.arani,
            stock_actual=1,
        )

    def _cobrar(self, usuario, detalles, metodo='efectivo', id_stripe=None):
        self.client.force_authenticate(usuario)
        cuerpo = {'metodo_pago': metodo, 'detalles': detalles}
        if id_stripe is not None:
            cuerpo['id_transaccion_stripe'] = id_stripe
        return self.client.post('/api/ventas/', cuerpo, format='json')


class PruebasRegistrarVenta(BaseVenta):
    def test_efectivo_descuenta_stock_y_deja_stripe_vacio(self):
        respuesta = self._cobrar(self.vendedor, [
            {'id_producto': self.marraqueta.id_producto, 'cantidad': 4},
            {'id_producto': self.arani.id_producto, 'cantidad': 1},
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total'], '3.00')
        self.assertEqual(respuesta.data['metodo_pago'], 'efectivo')
        self.assertIsNone(respuesta.data['id_transaccion_stripe'])
        self.assertEqual(respuesta.data['numero_comprobante'], 1)

        self.stock_marraqueta.refresh_from_db()
        self.stock_arani.refresh_from_db()
        self.assertEqual(self.stock_marraqueta.stock_actual, 6)
        self.assertEqual(self.stock_arani.stock_actual, 0)
        self.assertEqual(DetalleVenta.objects.count(), 2)
        self.assertEqual(
            MovimientoProductoTerminado.objects.filter(
                tipo=TipoMovimientoProductoTerminado.SALIDA,
                id_venta__isnull=False,
            ).count(),
            2,
        )
        self.assertTrue(Bitacora.objects.filter(accion=AccionBitacora.ALTA_VENTA).exists())

    def test_sin_stock_no_guarda_nada(self):
        respuesta = self._cobrar(self.vendedor, [
            {'id_producto': self.marraqueta.id_producto, 'cantidad': 2},
            {'id_producto': self.arani.id_producto, 'cantidad': 5},
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)
        self.stock_marraqueta.refresh_from_db()
        self.assertEqual(self.stock_marraqueta.stock_actual, 10)

    def test_produccion_no_puede_cobrar(self):
        respuesta = self._cobrar(self.produccion, [
            {'id_producto': self.marraqueta.id_producto, 'cantidad': 1},
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Venta.objects.count(), 0)

    def test_el_precio_queda_congelado(self):
        self._cobrar(self.vendedor, [
            {'id_producto': self.marraqueta.id_producto, 'cantidad': 2},
        ])
        self.marraqueta.precio_venta = Decimal('9.00')
        self.marraqueta.save(update_fields=['precio_venta', 'precio_sugerido'])
        detalle = DetalleVenta.objects.get()
        self.assertEqual(detalle.precio_unitario, Decimal('0.50'))
        self.assertEqual(detalle.subtotal, Decimal('1.00'))

    def test_qr_no_es_un_metodo_valido(self):
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 1}],
            metodo='qr',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)


@override_settings(STRIPE_SECRET_KEY='sk_test_cu13', STRIPE_CURRENCY='bob')
class PruebasVentaStripe(BaseVenta):
    def _intento(self, monto_centavos=100):
        intento = MagicMock()
        intento.id = 'pi_test_0001'
        intento.status = 'succeeded'
        intento.currency = 'bob'
        intento.amount = monto_centavos
        intento.client_secret = 'pi_test_0001_secret'
        return intento

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_stripe_guarda_el_id(self, stripe_mock):
        stripe_mock.PaymentIntent.retrieve.return_value = self._intento()
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 2}],
            metodo='stripe',
            id_stripe='pi_test_0001',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['metodo_pago'], 'stripe')
        self.assertEqual(respuesta.data['id_transaccion_stripe'], 'pi_test_0001')
        self.assertEqual(respuesta.data['total'], '1.00')

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_stripe_sin_id_no_guarda_la_venta(self, stripe_mock):
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 1}],
            metodo='stripe',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)
        stripe_mock.PaymentIntent.retrieve.assert_not_called()

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_stripe_sin_stock_anula_el_cobro(self, stripe_mock):
        stripe_mock.PaymentIntent.retrieve.return_value = self._intento(monto_centavos=500)
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.arani.id_producto, 'cantidad': 5}],
            metodo='stripe',
            id_stripe='pi_test_0001',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)
        stripe_mock.Refund.create.assert_called_once_with(payment_intent='pi_test_0001')
        self.stock_arani.refresh_from_db()
        self.assertEqual(self.stock_arani.stock_actual, 1)

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_crear_intencion_stripe_exitoso(self, stripe_mock):
        mock_pi = MagicMock()
        mock_pi.id = 'pi_test_crear_1'
        mock_pi.client_secret = 'pi_test_crear_1_secret'
        stripe_mock.PaymentIntent.create.return_value = mock_pi

        self.client.force_authenticate(self.vendedor)
        respuesta = self.client.post('/api/ventas/stripe/intencion/', {
            'detalles': [{'id_producto': self.marraqueta.id_producto, 'cantidad': 4}],
        }, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['id_transaccion_stripe'], 'pi_test_crear_1')
        self.assertEqual(respuesta.data['client_secret'], 'pi_test_crear_1_secret')
        self.assertEqual(respuesta.data['monto'], '2.00')
        self.assertEqual(respuesta.data['moneda'], 'bob')

    def test_crear_intencion_stripe_sin_stock_devuelve_400(self):
        self.client.force_authenticate(self.vendedor)
        respuesta = self.client.post('/api/ventas/stripe/intencion/', {
            'detalles': [{'id_producto': self.arani.id_producto, 'cantidad': 10}],
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_crear_intencion_stripe_monto_minimo_devuelve_400(self, stripe_mock):
        import stripe as real_stripe
        stripe_mock.error = real_stripe.error
        stripe_mock.PaymentIntent.create.side_effect = real_stripe.error.InvalidRequestError(
            'Amount must convert to at least 50 cents. Bs.0.50 converts to approximately $0.04.',
            param='amount',
        )

        self.client.force_authenticate(self.vendedor)
        respuesta = self.client.post('/api/ventas/stripe/intencion/', {
            'detalles': [{'id_producto': self.marraqueta.id_producto, 'cantidad': 1}],
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inferior al mínimo admitido', str(respuesta.data))

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_stripe_id_duplicado_rechaza_segunda_venta(self, stripe_mock):
        stripe_mock.PaymentIntent.retrieve.return_value = self._intento()
        # Primera venta exitosa
        resp1 = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 2}],
            metodo='stripe',
            id_stripe='pi_test_0001',
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Segunda venta con el mismo id_stripe
        resp2 = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 2}],
            metodo='stripe',
            id_stripe='pi_test_0001',
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 1)

    def test_efectivo_con_id_stripe_rechaza_con_400(self):
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 1}],
            metodo='efectivo',
            id_stripe='pi_test_no_debe_ir',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)

    @patch('apps.comercializacion.ventas.services.stripe_pago.stripe')
    def test_stripe_monto_incoherente_anula_cobro(self, stripe_mock):
        # Cobro en Stripe por Bs 5.00 pero en mostrador pide Bs 1.00 (2 marraquetas a 0.50)
        stripe_mock.PaymentIntent.retrieve.return_value = self._intento(monto_centavos=500)
        respuesta = self._cobrar(
            self.vendedor,
            [{'id_producto': self.marraqueta.id_producto, 'cantidad': 2}],
            metodo='stripe',
            id_stripe='pi_test_0001',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.count(), 0)
        stripe_mock.Refund.create.assert_called_once_with(payment_intent='pi_test_0001')
