"""
Pruebas para el Caso de Uso 21: Generar reporte de ventas.
Módulo: apps.reportes
Verifica agregaciones dinámicas, filtros de fecha/método, RBAC y exportación CSV/PDF.
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
from apps.productos_inventario.productos.models import Producto
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()


def _cuando(anio, mes, dia):
    return timezone.make_aware(datetime(anio, mes, dia, 10, 0))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasReporteVentas(TestCase):
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
            nombre_usuario='cvargas',
            password='PanADERIA2026!',
            nombre_completo='Carlos Vargas',
            email='dueno.reporte@mail.com',
            id_rol=rol,
        )
        self.ajeno = Usuario.objects.create_user(
            nombre_usuario='mrojas',
            password='PanADERIA2026!',
            nombre_completo='Miguel Rojas',
            email='horno.reporte@mail.com',
            id_rol=Rol.objects.create(nombre='Personal de Producción', descripcion='Horno'),
        )
        self.pan = Producto.objects.create(nombre='Marraqueta', precio_venta=Decimal('0.60'), activo=True)
        self._venta(1, _cuando(2026, 10, 15), 'efectivo', Decimal('6.00'), 10, self.pan)
        self._venta(2, _cuando(2026, 11, 2), 'stripe', Decimal('12.00'), 1, self.pan, stripe='pi_nov')

    def _venta(self, comprobante, cuando, metodo, total, cantidad, pan, stripe=None):
        venta = Venta.objects.create(
            id_usuario=self.propietario,
            numero_comprobante=comprobante,
            fecha_hora=cuando,
            metodo_pago=metodo,
            id_transaccion_stripe=stripe,
            total=total,
        )
        DetalleVenta.objects.create(
            id_venta=venta,
            id_producto=pan,
            cantidad=cantidad,
            precio_unitario=total,
            subtotal=total,
        )

    def test_octubre_no_incluye_noviembre(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '6.00')
        self.assertEqual(respuesta.data['efectivo'], '6.00')
        self.assertEqual(respuesta.data['tarjeta'], '0.00')

    def test_un_mes_vacio_devuelve_ceros(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-12-01',
            'hasta': '2026-12-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 0)
        self.assertEqual(respuesta.data['total'], '0.00')
        self.assertEqual(respuesta.data['productos'], [])

    def test_administrador_y_ventas_sin_el_permiso_reciben_403(self):
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        for indice, (rol_nombre, usuario_nombre) in enumerate(
            (('Administrador', 'adminrepo'), ('Personal de Ventas', 'mventas')),
            start=1,
        ):
            rol = Rol.objects.create(nombre=rol_nombre, descripcion='Sin reportes')
            persona = Usuario.objects.create_user(
                nombre_usuario=usuario_nombre,
                password='PanADERIA2026!',
                nombre_completo=rol_nombre,
                email=f'sin.reportes.{indice}@mail.com',
                id_rol=rol,
            )
            self.client.force_authenticate(persona)
            respuesta = self.client.get('/api/reportes/ventas/', consulta)
            self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_permiso_recibe_403(self):
        self.client.force_authenticate(self.ajeno)
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        self.assertEqual(self.client.get('/api/reportes/ventas/', consulta).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/reportes/ventas/csv/', consulta).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/reportes/ventas/pdf/', consulta).status_code, status.HTTP_403_FORBIDDEN)

    def test_el_csv_exporta_datos_dinamicos(self):
        self.client.force_authenticate(self.propietario)
        csv_respuesta = self.client.get('/api/reportes/ventas/csv/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(csv_respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', csv_respuesta['Content-Type'])
        texto = csv_respuesta.content.decode('utf-8-sig')
        self.assertIn('Reporte de ventas', texto)
        self.assertIn('6,00', texto)
        self.assertIn('Marraqueta', texto)
        self.assertIn('attachment; filename="reporte-ventas-2026-10-01-2026-10-31.csv"', csv_respuesta['Content-Disposition'])

    def test_el_pdf_exporta_datos_dinamicos(self):
        self.client.force_authenticate(self.propietario)
        pdf = self.client.get('/api/reportes/ventas/pdf/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertIn('attachment; filename="reporte-ventas-2026-10-01-2026-10-31.pdf"', pdf['Content-Disposition'])

    def test_sin_token_responde_401(self):
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        self.assertEqual(self.client.get('/api/reportes/ventas/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/ventas/csv/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/reportes/ventas/pdf/', consulta).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fecha_final_anterior_responde_400(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-31',
            'hasta': '2026-10-01',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hasta', respuesta.data)

    def test_metodo_desconocido_responde_400(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-01',
            'hasta': '2026-11-30',
            'metodo_pago': 'qr',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('metodo_pago', respuesta.data)

    def test_el_filtro_de_tarjeta_no_suma_el_efectivo(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-01',
            'hasta': '2026-11-30',
            'metodo_pago': 'stripe',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '12.00')
        self.assertEqual(respuesta.data['efectivo'], '0.00')
        self.assertEqual(respuesta.data['tarjeta'], '12.00')
        self.assertEqual(respuesta.data['productos'][0]['cantidad'], 1)
