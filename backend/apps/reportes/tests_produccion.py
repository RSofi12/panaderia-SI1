"""
Pruebas para el Caso de Uso 22: Generar reporte de producción.
Módulo: apps.reportes
Verifica agregaciones, comparativa vs ventas, filtro de jornada, RBAC y PDF/CSV.
"""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.comercializacion.ventas.models import DetalleVenta, Venta
from apps.productos_inventario.produccion.models import DetalleProduccion, JornadaProduccion, Produccion
from apps.productos_inventario.productos.models import Producto
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


def _cuando(anio, mes, dia):
    return timezone.make_aware(datetime(anio, mes, dia, 10, 0))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasReporteProduccion(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        permiso = Permiso.objects.create(
            nombre='generar_reportes',
            descripcion='Reportes',
            modulo=ModuloPermiso.REPORTES,
        )
        rol = Rol.objects.create(nombre='Propietario', descripcion='Dueño')
        RolPermiso.objects.create(rol=rol, permiso=permiso)
        self.propietario = Usuario.objects.create_user(
            nombre_usuario='cvargas_prod',
            password='PanADERIA2026!',
            nombre_completo='Carlos Vargas',
            email='dueno.produccion@mail.com',
            id_rol=rol,
        )
        self.ajeno = Usuario.objects.create_user(
            nombre_usuario='mventas_prod',
            password='PanADERIA2026!',
            nombre_completo='Mostrador',
            email='ventas.produccion@mail.com',
            id_rol=Rol.objects.create(nombre='Personal de Ventas', descripcion='Mostrador'),
        )
        self.marraqueta = Producto.objects.create(
            nombre='Marraqueta',
            precio_venta=Decimal('0.60'),
            activo=True,
        )
        self.semita = Producto.objects.create(
            nombre='Semita',
            precio_venta=Decimal('1.20'),
            activo=True,
        )
        self._lote(
            fecha=_cuando(2026, 10, 15).date(),
            jornada=JornadaProduccion.MANANA,
            lineas=((self.marraqueta, 40, Decimal('0.20')), (self.semita, 10, Decimal('0.40'))),
        )
        self._lote(
            fecha=_cuando(2026, 10, 15).date(),
            jornada=JornadaProduccion.TARDE,
            lineas=((self.marraqueta, 20, Decimal('0.20')),),
        )
        self._lote(
            fecha=_cuando(2026, 11, 2).date(),
            jornada=JornadaProduccion.NOCHE,
            lineas=((self.semita, 5, Decimal('0.40')),),
        )
        self._venta(1, _cuando(2026, 10, 15), self.marraqueta, 30, Decimal('18.00'))
        self._venta(2, _cuando(2026, 10, 16), self.semita, 4, Decimal('4.80'))

    def _lote(self, fecha, jornada, lineas):
        produccion = Produccion.objects.create(
            id_usuario=self.propietario,
            fecha=fecha,
            jornada=jornada,
        )
        for producto, cantidad, costo in lineas:
            DetalleProduccion.objects.create(
                id_produccion=produccion,
                id_producto=producto,
                cantidad_producida=cantidad,
                costo_unitario=costo,
            )
        return produccion

    def _venta(self, comprobante, cuando, producto, cantidad, total):
        venta = Venta.objects.create(
            id_usuario=self.propietario,
            numero_comprobante=comprobante,
            fecha_hora=cuando,
            metodo_pago='efectivo',
            total=total,
        )
        DetalleVenta.objects.create(
            id_venta=venta,
            id_producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
            subtotal=total,
        )

    def test_octubre_no_incluye_noviembre(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/produccion/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 2)
        self.assertEqual(respuesta.data['unidades'], 70)
        self.assertEqual(respuesta.data['unidades_vendidas'], 34)
        self.assertEqual(respuesta.data['diferencia'], 36)
        self.assertEqual(respuesta.data['costo'], '16.00')
        self.assertEqual(respuesta.data['manana'], 50)
        self.assertEqual(respuesta.data['tarde'], 20)
        self.assertEqual(respuesta.data['noche'], 0)
        nombres = {fila['nombre']: fila for fila in respuesta.data['productos']}
        self.assertEqual(nombres['Marraqueta']['cantidad'], 60)
        self.assertEqual(nombres['Marraqueta']['vendidas'], 30)
        self.assertEqual(nombres['Marraqueta']['diferencia'], 30)
        self.assertEqual(nombres['Semita']['cantidad'], 10)
        self.assertEqual(nombres['Semita']['vendidas'], 4)

    def test_un_mes_vacio_devuelve_ceros(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/produccion/', {
            'desde': '2026-12-01',
            'hasta': '2026-12-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 0)
        self.assertEqual(respuesta.data['unidades'], 0)
        self.assertEqual(respuesta.data['lotes'], [])
        self.assertEqual(respuesta.data['productos'], [])

    def test_filtro_de_jornada_no_suma_otras_tandas(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/produccion/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'jornada': 'Tarde',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['unidades'], 20)
        self.assertEqual(respuesta.data['tarde'], 20)
        self.assertEqual(respuesta.data['manana'], 0)
        # Las ventas siguen siendo del rango completo de fechas.
        self.assertEqual(respuesta.data['unidades_vendidas'], 34)

    def test_jornada_desconocida_responde_400(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/produccion/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'jornada': 'Madrugada',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('jornada', respuesta.data)

    def test_fecha_final_anterior_responde_400(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/produccion/', {
            'desde': '2026-10-31',
            'hasta': '2026-10-01',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hasta', respuesta.data)

    def test_sin_permiso_recibe_403(self):
        self.client.force_authenticate(self.ajeno)
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        self.assertEqual(self.client.get('/api/reportes/produccion/', consulta).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/reportes/produccion/csv/', consulta).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/reportes/produccion/pdf/', consulta).status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_token_responde_401(self):
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        self.assertEqual(self.client.get('/api/reportes/produccion/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/produccion/csv/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/produccion/pdf/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_el_csv_exporta_datos_dinamicos(self):
        self.client.force_authenticate(self.propietario)
        csv_respuesta = self.client.get('/api/reportes/produccion/csv/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(csv_respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', csv_respuesta['Content-Type'])
        texto = csv_respuesta.content.decode('utf-8-sig')
        self.assertIn('Reporte de producción', texto)
        self.assertIn('Marraqueta', texto)
        self.assertIn('16,00', texto)
        self.assertIn(
            'attachment; filename="reporte-produccion-2026-10-01-2026-10-31.csv"',
            csv_respuesta['Content-Disposition'],
        )

    def test_pdf_sin_produccion_responde_400(self):
        self.client.force_authenticate(self.propietario)
        pdf = self.client.get('/api/reportes/produccion/pdf/', {
            'desde': '2026-12-01',
            'hasta': '2026-12-31',
        })
        self.assertEqual(pdf.status_code, status.HTTP_400_BAD_REQUEST)

    def test_csv_sin_produccion_responde_400(self):
        self.client.force_authenticate(self.propietario)
        csv_respuesta = self.client.get('/api/reportes/produccion/csv/', {
            'desde': '2026-12-01',
            'hasta': '2026-12-31',
        })
        self.assertEqual(csv_respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_el_pdf_exporta_datos_dinamicos(self):
        self.client.force_authenticate(self.propietario)
        pdf = self.client.get('/api/reportes/produccion/pdf/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertIn(
            'attachment; filename="reporte-produccion-2026-10-01-2026-10-31.pdf"',
            pdf['Content-Disposition'],
        )


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], GEMINI_API_KEY='')
class PruebasVozReporteProduccion(TestCase):
    def setUp(self):
        self.client = APIClient()
        permiso = Permiso.objects.create(
            nombre='generar_reportes',
            descripcion='Reportes',
            modulo=ModuloPermiso.REPORTES,
        )
        rol = Rol.objects.create(nombre='Propietario', descripcion='Dueño')
        RolPermiso.objects.create(rol=rol, permiso=permiso)
        self.propietario = Usuario.objects.create_user(
            nombre_usuario='voz_prod',
            password='PanADERIA2026!',
            nombre_completo='Carlos Vargas',
            email='voz.prod@mail.com',
            id_rol=rol,
        )

    def test_interpretar_produccion_marca_modulo_disponible(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.post(
            '/api/reportes/voz/interpretar/',
            {'texto': 'Descarga en PDF el reporte de producción de este mes'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['caso_uso'], 'CU22')
        self.assertEqual(respuesta.data['formato'], 'pdf')
        self.assertTrue(respuesta.data['modulo_disponible'])
