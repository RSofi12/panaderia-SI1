from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import Permiso
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
        self.rol = Rol.objects.create(nombre='Operador', descripcion='Operador general')
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='user_mp',
            email='user_mp@panaderia.com',
            nombre_completo='Usuario MP',
            password='Password123!',
            id_rol=self.rol,
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

    def test_crear_materia_prima_requiere_permiso_y_crea_stock_en_cero(self):
        self.client.force_authenticate(user=self.usuario)
        url = reverse('productos_inventario:materias_primas')
        payload = {
            'nombre': 'Azúcar',
            'unidad_medida': 'kg',
            'stock_minimo': '5.000',
        }

        sin_permiso = self.client.post(url, payload)
        self.assertEqual(sin_permiso.status_code, status.HTTP_403_FORBIDDEN)

        permiso, _ = Permiso.objects.get_or_create(
            nombre='gestionar_materias_primas',
            defaults={'modulo': 'productos_inventario'},
        )
        self.rol.asignar_permiso(permiso)
        respuesta = self.client.post(url, payload)

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        materia = MateriaPrima.objects.get(nombre='Azúcar')
        self.assertEqual(materia.inventario.stock_actual, Decimal('0'))
        self.assertEqual(respuesta.data['activo'], True)
        self.assertTrue(Bitacora.objects.filter(
            accion=AccionBitacora.ALTA_MATERIA_PRIMA,
            tabla_afectada='materia_prima',
        ).exists())

    def test_rechazar_nombre_duplicado_y_stock_minimo_negativo(self):
        permiso, _ = Permiso.objects.get_or_create(
            nombre='gestionar_materias_primas',
            defaults={'modulo': 'productos_inventario'},
        )
        self.rol.asignar_permiso(permiso)
        self.client.force_authenticate(user=self.usuario)
        url = reverse('productos_inventario:materias_primas')

        duplicada = self.client.post(url, {
            'nombre': 'harina especial',
            'unidad_medida': 'kg',
            'stock_minimo': '1.000',
        })
        negativa = self.client.post(url, {
            'nombre': 'Azúcar',
            'unidad_medida': 'kg',
            'stock_minimo': '-1.000',
        })

        self.assertEqual(duplicada.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(negativa.status_code, status.HTTP_400_BAD_REQUEST)

    def test_editar_catalogo_y_inactivar_sin_eliminar_materia_prima(self):
        permiso, _ = Permiso.objects.get_or_create(
            nombre='gestionar_materias_primas',
            defaults={'modulo': 'productos_inventario'},
        )
        self.rol.asignar_permiso(permiso)
        self.client.force_authenticate(user=self.usuario)

        detalle = reverse(
            'productos_inventario:materia_prima_detalle',
            args=[self.materia.id_materia_prima],
        )
        respuesta_edicion = self.client.patch(detalle, {
            'nombre': 'Harina Premium',
            'unidad_medida': 'kg',
            'stock_minimo': '12.500',
        })
        self.assertEqual(respuesta_edicion.status_code, status.HTTP_200_OK)
        self.materia.refresh_from_db()
        self.assertEqual(self.materia.nombre, 'Harina Premium')
        self.assertEqual(self.materia.stock_minimo, Decimal('12.500'))
        self.assertEqual(self.materia.inventario.stock_actual, Decimal('50.000'))

        estado = reverse(
            'productos_inventario:materia_prima_toggle_activo',
            args=[self.materia.id_materia_prima],
        )
        respuesta_estado = self.client.patch(estado)
        self.assertEqual(respuesta_estado.status_code, status.HTTP_200_OK)
        self.materia.refresh_from_db()
        self.assertFalse(self.materia.activo)
        self.assertTrue(MateriaPrima.objects.filter(pk=self.materia.pk).exists())
        self.assertTrue(Bitacora.objects.filter(
            accion=AccionBitacora.EDICION_MATERIA_PRIMA,
        ).exists())
        self.assertTrue(Bitacora.objects.filter(
            accion=AccionBitacora.CAMBIAR_ESTADO_MATERIA_PRIMA,
        ).exists())

    def test_filtrar_materias_primas_inactivas(self):
        self.materia.activo = False
        self.materia.save(update_fields=['activo'])
        self.client.force_authenticate(user=self.usuario)

        respuesta = self.client.get(
            reverse('productos_inventario:materias_primas_stock'),
            {'activo': 'false'},
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertFalse(respuesta.data[0]['activo'])
