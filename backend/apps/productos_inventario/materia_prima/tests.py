from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.roles.models import Rol
from apps.usuarios_seguridad.permisos.models import Permiso
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


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasAlertasBajoStock(TestCase):
    """Pruebas de CU09: consultar alertas de bajo stock."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('productos_inventario:alertas_bajo_stock')

        self.permiso_inventario = Permiso.objects.create(
            nombre='gestionar_inventario',
            modulo='productos_inventario',
            descripcion='Consultar y gestionar inventario',
        )

        self.propietario = self.crear_usuario(
            'usuario_propietario_cu09',
            'Propietario',
            asignar_permiso=True,
        )
        self.produccion = self.crear_usuario(
            'usuario_produccion_cu09',
            'Personal de Producción',
            asignar_permiso=True,
        )
        self.ventas = self.crear_usuario(
            'usuario_ventas_cu09',
            'Personal de Ventas',
            asignar_permiso=True,
        )

    def crear_usuario(self, nombre_usuario, nombre_rol, asignar_permiso):
        rol = Rol.objects.create(
            nombre=nombre_rol,
            descripcion=f'Rol de prueba CU09: {nombre_usuario}',
        )

        if asignar_permiso:
            rol.permisos.add(self.permiso_inventario)

        return Usuario.objects.create_user(
            nombre_usuario=nombre_usuario,
            email=f'{nombre_usuario}@panaderia.com',
            nombre_completo=nombre_usuario,
            password='Password123!',
            id_rol=rol,
        )

    def crear_materia(self, nombre, stock_actual, stock_minimo, activo=True):
        materia = MateriaPrima.objects.create(
            nombre=nombre,
            unidad_medida='kg',
            stock_minimo=Decimal(stock_minimo),
            activo=activo,
        )
        InventarioMateriaPrima.objects.create(
            id_materia_prima=materia,
            stock_actual=Decimal(stock_actual),
        )
        return materia

    def test_detecta_solamente_materias_con_bajo_stock(self):
        self.crear_materia('Harina', '3.000', '10.000')
        self.crear_materia('Azucar', '15.000', '10.000')
        self.crear_materia('Levadura', '2.000', '5.000')

        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 2)

        nombres = {item['nombre'] for item in respuesta.data}
        self.assertEqual(nombres, {'Harina', 'Levadura'})

        harina = next(
            item for item in respuesta.data
            if item['nombre'] == 'Harina'
        )
        self.assertEqual(harina['stock_actual'], '3.000')
        self.assertEqual(harina['stock_minimo'], '10.000')
        self.assertEqual(harina['faltante'], '7.000')

    def test_stock_igual_al_minimo_no_genera_alerta(self):
        self.crear_materia('Sal', '5.000', '5.000')

        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, [])

    def test_materia_inactiva_no_aparece(self):
        self.crear_materia(
            'Insumo inactivo',
            '1.000',
            '10.000',
            activo=False,
        )

        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, [])

    def test_materia_sin_inventario_utiliza_stock_cero(self):
        MateriaPrima.objects.create(
            nombre='Cacao',
            unidad_medida='kg',
            stock_minimo=Decimal('4.000'),
            activo=True,
        )

        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(respuesta.data[0]['stock_actual'], '0.000')
        self.assertEqual(respuesta.data[0]['faltante'], '4.000')

    def test_propietario_y_produccion_tienen_acceso(self):
        for usuario in (self.propietario, self.produccion):
            with self.subTest(usuario=usuario.nombre_usuario):
                self.client.force_authenticate(user=usuario)
                respuesta = self.client.get(self.url)
                self.assertEqual(
                    respuesta.status_code,
                    status.HTTP_200_OK,
                )

    def test_ventas_no_tiene_acceso_aunque_tenga_permiso(self):
        self.client.force_authenticate(user=self.ventas)
        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_propietario_sin_permiso_no_tiene_acceso(self):
        self.propietario.id_rol.permisos.remove(
            self.permiso_inventario
        )

        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_usuario_no_autenticado_no_tiene_acceso(self):
        respuesta = self.client.get(self.url)

        self.assertIn(
            respuesta.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_administrador_con_permiso_tiene_acceso(self):
        usuario = self.crear_usuario('admin_cu09', 'Administrador', True)
        self.client.force_authenticate(user=usuario)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_minimo_cero_sin_inventario_no_genera_alerta(self):
        MateriaPrima.objects.create(nombre='Agua', unidad_medida='l', stock_minimo=0)
        self.client.force_authenticate(user=self.propietario)
        self.assertEqual(self.client.get(self.url).data, [])

    def test_diferencia_de_una_milesima_genera_alerta(self):
        self.crear_materia('Harina fina', '4.999', '5.000')
        self.client.force_authenticate(user=self.propietario)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data[0]['faltante'], '0.001')

    def test_endpoint_solo_permite_consulta(self):
        self.client.force_authenticate(user=self.propietario)
        self.assertEqual(self.client.post(self.url, {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
