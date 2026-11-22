"""CU21: el mes suma ventas ya guardadas y no mezcla otro mes."""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.comercializacion.ventas.models import DetalleVenta, Venta
from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.compras.proveedores.models import Proveedor
from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.productos.models import Producto
from apps.reportes.models import CierreReporteCompras, CierreReporteVentas
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
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
        respuesta = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        csv_respuesta = self.client.get('/api/reportes/ventas/csv/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(csv_respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_el_cierre_guarda_el_total_y_el_dinamico_sigue_cambiando(self):
        self.client.force_authenticate(self.propietario)
        guardado = self.client.post('/api/reportes/ventas/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'periodo': 'mes',
        }, format='json')
        self.assertEqual(guardado.status_code, status.HTTP_201_CREATED)
        self.assertEqual(guardado.data['total'], '6.00')
        self.assertEqual(guardado.data['productos'][0]['nombre'], 'Marraqueta')
        self.assertTrue(
            Bitacora.objects.filter(accion=AccionBitacora.CIERRE_REPORTE_VENTAS).exists()
        )

        self._venta(3, _cuando(2026, 10, 20), 'efectivo', Decimal('3.00'), 2, self.pan)
        vivo = self.client.get('/api/reportes/ventas/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(vivo.data['total'], '9.00')

        fijo = self.client.get(f'/api/reportes/ventas/cierres/{guardado.data["id_cierre"]}/')
        self.assertEqual(fijo.status_code, status.HTTP_200_OK)
        self.assertEqual(fijo.data['total'], '6.00')
        self.assertEqual(fijo.data['cantidad'], 1)
        self.assertEqual(CierreReporteVentas.objects.get().total, Decimal('6.00'))

    def test_el_csv_recalcula_y_el_pdf_conserva_el_cierre(self):
        self.client.force_authenticate(self.propietario)
        guardado = self.client.post('/api/reportes/ventas/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'periodo': 'mes',
        }, format='json')
        self._venta(4, _cuando(2026, 10, 21), 'efectivo', Decimal('3.00'), 1, self.pan)

        csv_respuesta = self.client.get('/api/reportes/ventas/csv/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(csv_respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', csv_respuesta['Content-Type'])
        texto = csv_respuesta.content.decode('utf-8-sig')
        self.assertIn('9.00', texto)
        self.assertIn('Marraqueta', texto)
        self.assertIn('attachment; filename="reporte-ventas-2026-10-01-2026-10-31.csv"', csv_respuesta['Content-Disposition'])

        pdf = self.client.get(f'/api/reportes/ventas/cierres/{guardado.data["id_cierre"]}/pdf/')
        self.assertEqual(pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertIn(b'6.00', pdf.content)
        self.assertNotIn(b'9.00', pdf.content)

        self.client.force_authenticate(self.ajeno)
        prohibido = self.client.get(f'/api/reportes/ventas/cierres/{guardado.data["id_cierre"]}/pdf/')
        self.assertEqual(prohibido.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_token_responde_401(self):
        consulta = {'desde': '2026-10-01', 'hasta': '2026-10-31'}
        reporte = self.client.get('/api/reportes/ventas/', consulta)
        csv_respuesta = self.client.get('/api/reportes/ventas/csv/', consulta)
        cierre = self.client.post('/api/reportes/ventas/cierres/', {
            **consulta,
            'periodo': 'mes',
        }, format='json')
        self.assertEqual(reporte.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(csv_respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(cierre.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(CierreReporteVentas.objects.count(), 0)

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

        guardado = self.client.post('/api/reportes/ventas/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-11-30',
            'periodo': 'mes',
            'metodo_pago': 'stripe',
        }, format='json')
        self.assertEqual(guardado.status_code, status.HTTP_201_CREATED)
        self.assertEqual(guardado.data['total'], '12.00')
        self.assertEqual(guardado.data['metodo_pago'], 'stripe')
        self.assertEqual(guardado.data['efectivo'], '0.00')

    def test_cierre_inexistente_responde_404(self):
        self.client.force_authenticate(self.propietario)
        detalle = self.client.get('/api/reportes/ventas/cierres/99999/')
        pdf = self.client.get('/api/reportes/ventas/cierres/99999/pdf/')
        self.assertEqual(detalle.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(pdf.status_code, status.HTTP_404_NOT_FOUND)


# ==============================================================================
# CU24: Generar reporte de compras y gastos
# ==============================================================================

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PruebasReporteCompras(TestCase):
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
            email='dueno.compras@mail.com',
            id_rol=rol,
        )
        self.ajeno = Usuario.objects.create_user(
            nombre_usuario='mrojas',
            password='PanADERIA2026!',
            nombre_completo='Miguel Rojas',
            email='horno.compras@mail.com',
            id_rol=Rol.objects.create(nombre='Personal de Producción', descripcion='Horno'),
        )

        self.proveedor_a = Proveedor.objects.create(nombre='Molino Central SRL', telefono='77112233')
        self.proveedor_b = Proveedor.objects.create(nombre='Distribuidora Láctea', telefono='77445566')

        self.harina = MateriaPrima.objects.create(
            nombre='Harina de Trigo 000',
            unidad_medida='kg',
            stock_minimo=Decimal('10.000'),
        )
        self.azucar = MateriaPrima.objects.create(
            nombre='Azúcar Blanca Refinada',
            unidad_medida='kg',
            stock_minimo=Decimal('5.000'),
        )

        # Compra 1: Octubre 2026 (Molino Central, Harina 100kg = Bs 550)
        self._compra(
            proveedor=self.proveedor_a,
            cuando=_cuando(2026, 10, 10),
            total=Decimal('550.00'),
            detalles=[(self.harina, Decimal('100.000'), Decimal('5.50'), Decimal('550.00'))],
        )

        # Compra 2: Noviembre 2026 (Distribuidora Láctea, Azúcar 50kg = Bs 300)
        self._compra(
            proveedor=self.proveedor_b,
            cuando=_cuando(2026, 11, 5),
            total=Decimal('300.00'),
            detalles=[(self.azucar, Decimal('50.000'), Decimal('6.00'), Decimal('300.00'))],
        )

    def _compra(self, proveedor, cuando, total, detalles):
        compra = Compra.objects.create(
            id_proveedor=proveedor,
            id_usuario=self.propietario,
            fecha_hora=cuando,
            total=total,
        )
        for insumo, cant, precio, subtotal in detalles:
            DetalleCompra.objects.create(
                id_compra=compra,
                id_materia_prima=insumo,
                cantidad=cant,
                precio_unitario=precio,
                subtotal=subtotal,
            )
        return compra

    def test_sin_permiso_responde_403(self):
        self.client.force_authenticate(self.ajeno)
        respuesta = self.client.get('/api/reportes/compras/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_fechas_invertidas_responde_400(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/compras/', {
            'desde': '2026-11-30',
            'hasta': '2026-11-01',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hasta', respuesta.data)

    def test_reporte_dinamico_suma_compras_del_periodo(self):
        self.client.force_authenticate(self.propietario)
        # Consultar octubre 2026
        respuesta = self.client.get('/api/reportes/compras/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '550.00')
        self.assertEqual(len(respuesta.data['proveedores']), 1)
        self.assertEqual(respuesta.data['proveedores'][0]['nombre'], 'Molino Central SRL')
        self.assertEqual(len(respuesta.data['insumos']), 1)
        self.assertEqual(respuesta.data['insumos'][0]['nombre'], 'Harina de Trigo 000')

    def test_filtro_por_proveedor(self):
        self.client.force_authenticate(self.propietario)
        # Rango amplio pero filtrando solo Proveedor B
        respuesta = self.client.get('/api/reportes/compras/', {
            'desde': '2026-09-01',
            'hasta': '2026-11-30',
            'id_proveedor': self.proveedor_b.pk,
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '300.00')
        self.assertEqual(respuesta.data['proveedores'][0]['nombre'], 'Distribuidora Láctea')

    def test_filtro_por_materia_prima(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/compras/', {
            'desde': '2026-09-01',
            'hasta': '2026-11-30',
            'id_materia_prima': self.harina.pk,
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '550.00')
        self.assertEqual(respuesta.data['insumos'][0]['nombre'], 'Harina de Trigo 000')

    def test_guardar_cierre_compras_congela_y_audita_en_bitacora(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.post('/api/reportes/compras/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'periodo': 'mes',
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['cantidad'], 1)
        self.assertEqual(respuesta.data['total'], '550.00')
        self.assertEqual(len(respuesta.data['insumos']), 1)
        self.assertEqual(respuesta.data['insumos'][0]['nombre'], 'Harina de Trigo 000')

        # Verificar auditoría en Bitácora
        evento = Bitacora.objects.filter(accion=AccionBitacora.CIERRE_REPORTE_COMPRAS).latest('id_bitacora')
        self.assertEqual(evento.usuario, self.propietario)
        self.assertIn('550.00', evento.descripcion)

    def test_cierre_compras_no_se_recalcula_si_entra_compra_nueva(self):
        self.client.force_authenticate(self.propietario)
        # Crear cierre
        creacion = self.client.post('/api/reportes/compras/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'periodo': 'mes',
        }, format='json')
        id_cierre = creacion.data['id_cierre']

        # Entra compra posterior en el mismo mes cerrado
        self._compra(
            proveedor=self.proveedor_a,
            cuando=_cuando(2026, 10, 28),
            total=Decimal('200.00'),
            detalles=[(self.harina, Decimal('36.000'), Decimal('5.50'), Decimal('200.00'))],
        )

        # La consulta del cierre estático guardado sigue diciendo 550.00
        detalle = self.client.get(f'/api/reportes/compras/cierres/{id_cierre}/')
        self.assertEqual(detalle.status_code, status.HTTP_200_OK)
        self.assertEqual(detalle.data['total'], '550.00')
        self.assertEqual(detalle.data['cantidad'], 1)

        # Pero el reporte dinámico ahora sí suma 750.00
        dinamico = self.client.get('/api/reportes/compras/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(dinamico.data['total'], '750.00')
        self.assertEqual(dinamico.data['cantidad'], 2)

    def test_descargar_csv_compras(self):
        self.client.force_authenticate(self.propietario)
        respuesta = self.client.get('/api/reportes/compras/csv/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('reporte-compras-2026-10-01-2026-10-31.csv', respuesta['Content-Disposition'])

    def test_descargar_pdf_cierre_compras(self):
        self.client.force_authenticate(self.propietario)
        creacion = self.client.post('/api/reportes/compras/cierres/', {
            'desde': '2026-10-01',
            'hasta': '2026-10-31',
            'periodo': 'mes',
        }, format='json')
        id_cierre = creacion.data['id_cierre']

        respuesta = self.client.get(f'/api/reportes/compras/cierres/{id_cierre}/pdf/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

