from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.productos_inventario.productos.models import CategoriaProducto, Producto
from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasConsultarDisponibilidadCU17(TestCase):
    def setUp(self):
        permiso = Permiso.objects.create(
            nombre='registrar_ventas',
            descripcion='Consultar disponibilidad para ventas',
            modulo=ModuloPermiso.COMERCIALIZACION,
        )
        rol = Rol.objects.create(nombre='Personal de Ventas', descripcion='Ventas')
        RolPermiso.objects.create(rol=rol, permiso=permiso)
        usuario_model = get_user_model()
        self.usuario = usuario_model.objects.create_user(
            nombre_usuario='ventas_cu17',
            password='PanADERIA2026!',
            nombre_completo='Ventas CU17',
            email='ventas-cu17@mail.com',
            id_rol=rol,
        )
        self.categoria = CategoriaProducto.objects.create(nombre='Panes CU17')
        self.disponible = Producto.objects.create(
            nombre='Marraqueta CU17',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        self.agotado = Producto.objects.create(
            nombre='Agotado CU17',
            id_categoria=self.categoria,
            costo_produccion=Decimal('0.40'),
            porcentaje_ganancia=Decimal('50.00'),
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        InventarioProductoTerminado.objects.create(id_producto=self.disponible, stock_actual=10)
        InventarioProductoTerminado.objects.create(id_producto=self.agotado, stock_actual=0)
        self.client = APIClient()
        self.client.force_authenticate(self.usuario)

    def test_solo_devuelve_productos_activos_con_stock(self):
        respuesta = self.client.get('/api/disponibilidad/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual([item['nombre'] for item in respuesta.data], ['Marraqueta CU17'])

    def test_filtra_por_nombre_y_categoria(self):
        respuesta = self.client.get('/api/disponibilidad/', {
            'q': 'Marraqueta',
            'categoria': str(self.categoria.id_categoria),
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
