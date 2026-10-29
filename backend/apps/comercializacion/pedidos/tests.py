"""
Pruebas del CU14 — alta de pedido.

El pedido nace pendiente. No crea venta y no descuenta stock.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.comercializacion.pedidos.models import Cliente, DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.models import DetalleVenta, Venta
from apps.productos_inventario.productos.models import Producto
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BasePedido(TestCase):
    def setUp(self):
        self.client = APIClient()
        permiso = Permiso.objects.create(
            nombre='registrar_pedidos',
            descripcion='Registrar pedidos',
            modulo=ModuloPermiso.COMERCIALIZACION,
        )
        rol_ventas = Rol.objects.create(nombre='Personal de Ventas', descripcion='Mostrador')
        RolPermiso.objects.create(rol=rol_ventas, permiso=permiso)
        rol_produccion = Rol.objects.create(nombre='Personal de Producción', descripcion='Horno')

        self.vendedor = Usuario.objects.create_user(
            nombre_usuario='mgonzales',
            password='PanADERIA2026!',
            nombre_completo='María Gonzales',
            email='ventas.pedido@mail.com',
            id_rol=rol_ventas,
        )
        self.produccion = Usuario.objects.create_user(
            nombre_usuario='mrojas',
            password='PanADERIA2026!',
            nombre_completo='Miguel Rojas',
            email='produccion.pedido@mail.com',
            id_rol=rol_produccion,
        )
        self.marraqueta = Producto.objects.create(
            nombre='Marraqueta',
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        self.inactivo = Producto.objects.create(
            nombre='Pan viejo',
            precio_venta=Decimal('1.00'),
            activo=False,
        )
        self.stock = InventarioProductoTerminado.objects.create(
            id_producto=self.marraqueta,
            stock_actual=40,
        )
        self.cliente = Cliente.objects.create(nombre='Rosa Fernández', telefono='70011122')

    def _pedir(self, usuario, cuerpo):
        self.client.force_authenticate(usuario)
        return self.client.post('/api/pedidos/', cuerpo, format='json')

    def _cambiar(self, usuario, pedido_id, estado):
        self.client.force_authenticate(usuario)
        return self.client.patch(
            f'/api/pedidos/{pedido_id}/',
            {'estado': estado},
            format='json',
        )

    def _cuerpo(self, **extra):
        cuerpo = {
            'cliente': {'nombre': 'Hotel Cortez', 'telefono': '33421100'},
            'fecha_entrega': '2026-09-07T07:00:00Z',
            'metodo_pago': 'efectivo',
            'detalles': [{'id_producto': self.marraqueta.id_producto, 'cantidad': 10}],
        }
        cuerpo.update(extra)
        return cuerpo


class PruebasRegistrarPedido(BasePedido):
    def test_alta_crea_cliente_pedido_pendiente_y_bitacora(self):
        respuesta = self._pedir(self.vendedor, self._cuerpo())
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['estado'], EstadoPedido.PENDIENTE)
        self.assertEqual(respuesta.data['total'], '6.00')
        self.assertEqual(respuesta.data['cliente'], 'Hotel Cortez')
        self.assertEqual(respuesta.data['detalles'][0]['precio_unitario'], '0.60')
        self.assertEqual(Cliente.objects.filter(nombre='Hotel Cortez').count(), 1)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(DetallePedido.objects.count(), 1)
        self.assertEqual(Venta.objects.count(), 0)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.stock_actual, 40)
        self.assertTrue(Bitacora.objects.filter(accion=AccionBitacora.ALTA_PEDIDO).exists())

    def test_reutiliza_cliente_existente(self):
        respuesta = self._pedir(self.vendedor, self._cuerpo(cliente={'id_cliente': self.cliente.id_cliente}))
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['id_cliente'], self.cliente.id_cliente)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_producto_inactivo_no_guarda_nada(self):
        respuesta = self._pedir(self.vendedor, self._cuerpo(detalles=[
            {'id_producto': self.inactivo.id_producto, 'cantidad': 2},
        ]))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(Cliente.objects.filter(nombre='Hotel Cortez').count(), 0)

    def test_produccion_recibe_403(self):
        respuesta = self._pedir(self.produccion, self._cuerpo())
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_detalle_devuelve_el_pedido(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        respuesta = self.client.get(f"/api/pedidos/{alta.data['id_pedido']}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], 'pendiente')
        self.assertEqual(len(respuesta.data['detalles']), 1)


class PruebasCambiarEstadoPedido(BasePedido):
    def test_pendiente_pasa_a_preparacion_sin_venta_ni_stock(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        respuesta = self._cambiar(self.vendedor, alta.data['id_pedido'], 'en_preparacion')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], EstadoPedido.EN_PREPARACION)
        self.assertEqual(Venta.objects.count(), 0)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.stock_actual, 40)
        self.assertTrue(
            Bitacora.objects.filter(accion=AccionBitacora.CAMBIAR_ESTADO_PEDIDO).exists()
        )

    def test_avanza_a_listo_y_se_puede_cancelar(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        pedido_id = alta.data['id_pedido']
        preparacion = self._cambiar(self.vendedor, pedido_id, 'en_preparacion')
        listo = self._cambiar(self.vendedor, pedido_id, 'listo')
        cancelado = self._cambiar(self.vendedor, pedido_id, 'cancelado')
        self.assertEqual(preparacion.status_code, status.HTTP_200_OK)
        self.assertEqual(listo.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelado.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelado.data['estado'], EstadoPedido.CANCELADO)
        self.assertEqual(Venta.objects.count(), 0)

    def test_entregado_se_rechaza_y_el_estado_no_cambia(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        respuesta = self._cambiar(self.vendedor, alta.data['id_pedido'], 'entregado')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        pedido = Pedido.objects.get(pk=alta.data['id_pedido'])
        self.assertEqual(pedido.estado, EstadoPedido.PENDIENTE)
        self.assertEqual(Venta.objects.count(), 0)

    def test_produccion_no_cambia_el_estado(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        respuesta = self._cambiar(self.produccion, alta.data['id_pedido'], 'en_preparacion')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        pedido = Pedido.objects.get(pk=alta.data['id_pedido'])
        self.assertEqual(pedido.estado, EstadoPedido.PENDIENTE)

    def test_el_listado_oculta_el_cancelado(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        lista = self.client.get('/api/pedidos/')
        self.assertEqual(lista.status_code, status.HTTP_200_OK)
        self.assertEqual(len(lista.data), 1)
        self._cambiar(self.vendedor, alta.data['id_pedido'], 'cancelado')
        lista = self.client.get('/api/pedidos/')
        self.assertEqual(lista.data, [])

    def _dejar_listo(self):
        alta = self._pedir(self.vendedor, self._cuerpo())
        pedido_id = alta.data['id_pedido']
        self._cambiar(self.vendedor, pedido_id, 'en_preparacion')
        self._cambiar(self.vendedor, pedido_id, 'listo')
        return pedido_id

    def test_entregar_crea_una_venta_y_descuenta_stock(self):
        pedido_id = self._dejar_listo()
        self.marraqueta.precio_venta = Decimal('5.00')
        self.marraqueta.save(update_fields=['precio_venta'])
        respuesta = self._cambiar(self.vendedor, pedido_id, 'entregado')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], EstadoPedido.ENTREGADO)
        venta = Venta.objects.get(id_pedido_id=pedido_id)
        self.assertEqual(venta.total, Decimal('6.00'))
        self.assertEqual(venta.metodo_pago, 'efectivo')
        self.assertIsNone(venta.id_transaccion_stripe)
        detalle = DetalleVenta.objects.get(id_venta=venta)
        self.assertEqual(detalle.precio_unitario, Decimal('0.60'))
        self.assertEqual(detalle.cantidad, 10)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.stock_actual, 30)
        movimiento = MovimientoProductoTerminado.objects.get(id_venta=venta)
        self.assertEqual(movimiento.id_pedido_id, pedido_id)
        self.assertEqual(movimiento.cantidad, 10)
        self.assertTrue(Bitacora.objects.filter(accion=AccionBitacora.ALTA_VENTA).exists())
        lista = self.client.get('/api/pedidos/')
        self.assertEqual(lista.data, [])
        repetido = self._cambiar(self.vendedor, pedido_id, 'entregado')
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Venta.objects.filter(id_pedido_id=pedido_id).count(), 1)

    def test_tarjeta_sin_datos_no_entrega_ni_crea_venta(self):
        alta = self._pedir(self.vendedor, self._cuerpo(metodo_pago='stripe'))
        pedido_id = alta.data['id_pedido']
        self._cambiar(self.vendedor, pedido_id, 'en_preparacion')
        self._cambiar(self.vendedor, pedido_id, 'listo')
        respuesta = self._cambiar(self.vendedor, pedido_id, 'entregado')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        pedido = Pedido.objects.get(pk=pedido_id)
        self.assertEqual(pedido.estado, EstadoPedido.LISTO)
        self.assertEqual(Venta.objects.count(), 0)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.stock_actual, 40)
