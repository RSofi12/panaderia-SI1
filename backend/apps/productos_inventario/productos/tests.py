from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
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
