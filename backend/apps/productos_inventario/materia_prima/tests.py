from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.roles.models import Rol
from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
)

Usuario = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasMateriaPrima(TestCase):
    def setUp(self):
        self.client = APIClient()
        rol = Rol.objects.create(nombre='Operador', descripcion='Operador general')
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='user_mp',
            email='user_mp@panaderia.com',
            nombre_completo='Usuario MP',
            password='Password123!',
            id_rol=rol,
        )
        self.materia = MateriaPrima.objects.create(
            nombre='Harina Especial',
            unidad_medida='kg',
            stock_minimo=Decimal('10.000'),
            activo=True,
        )
        InventarioMateriaPrima.objects.create(
            id_materia_prima=self.materia,
            stock_actual=Decimal('50.000'),
        )
        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=self.materia,
            precio=Decimal('4.50'),
        )

    def test_listar_materias_primas_con_stock_y_precio(self):
        self.client.force_authenticate(user=self.usuario)
        url = reverse('productos_inventario:materias_primas')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        item = res.data[0]
        self.assertEqual(item['nombre'], 'Harina Especial')
        self.assertEqual(item['stock_actual'], '50.000')
        self.assertEqual(item['precio_ultima_compra'], '4.50')
