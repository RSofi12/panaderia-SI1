"""
Pruebas del CU20 — Registrar gasto o inversión.

Cubre:
    - Alta de gasto e inversión (201 + bitácora ALTA_MOVIMIENTO_ECONOMICO)
    - Validaciones: monto > 0, 2 decimales, tipo/categoría válidos, fecha no futura
    - El responsable sale de la sesión, nunca del payload
    - RBAC: 403 sin permiso, 401 sin autenticación
    - Rollback completo si falla la bitácora
    - Listado con filtros y exclusión de anulados
    - Anulación (sin borrar), doble anulación y 404
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.compras.gastos.models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)
from apps.compras.gastos.services.registrar_movimiento import registrar_movimiento
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import ModuloPermiso, Permiso
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso

Usuario = get_user_model()

URL_LISTA = '/api/gastos/'


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BasePruebasGastos(TestCase):
    def setUp(self):
        self.client = APIClient()

        permiso = Permiso.objects.create(
            nombre='registrar_gastos',
            descripcion='Registrar gastos e inversiones',
            modulo=ModuloPermiso.COMPRAS,
        )
        rol_propietario = Rol.objects.create(nombre='Propietario', descripcion='Dueño')
        RolPermiso.objects.create(rol=rol_propietario, permiso=permiso)

        rol_sin_acceso = Rol.objects.create(nombre='Sin Acceso', descripcion='Ninguno')

        self.propietario = Usuario.objects.create_user(
            nombre_usuario='propietario',
            password='Password123!',
            nombre_completo='Carlos Santiago Vargas',
            email='propietario@mail.com',
            id_rol=rol_propietario,
        )
        self.sin_permiso = Usuario.objects.create_user(
            nombre_usuario='sin_permiso',
            password='Password123!',
            nombre_completo='Sin Permiso',
            email='sinpermiso@mail.com',
            id_rol=rol_sin_acceso,
        )

    def payload(self, **cambios):
        datos = {
            'tipo': TipoMovimientoEconomico.GASTO,
            'categoria': CategoriaMovimientoEconomico.SERVICIOS,
            'concepto': 'Energía eléctrica',
            'monto': '350.00',
            'descripcion': 'Factura de octubre',
        }
        datos.update(cambios)
        return datos

    def crear_movimiento(self, **cambios):
        datos = {
            'id_usuario': self.propietario,
            'tipo': TipoMovimientoEconomico.GASTO,
            'categoria': CategoriaMovimientoEconomico.SERVICIOS,
            'concepto': 'Energía eléctrica',
            'monto': '350.00',
        }
        datos.update(cambios)
        return MovimientoEconomico.objects.create(**datos)


class PruebasRegistroGasto(BasePruebasGastos):
    def test_registrar_gasto_valido_deja_bitacora(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(), format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['tipo'], 'gasto')
        self.assertEqual(res.data['tipo_display'], 'Gasto operativo')
        self.assertEqual(res.data['categoria'], 'servicios')
        self.assertEqual(res.data['concepto'], 'Energía eléctrica')
        self.assertEqual(res.data['monto'], '350.00')
        self.assertFalse(res.data['anulado'])
        self.assertEqual(res.data['registrado_por'], 'propietario')

        self.assertEqual(MovimientoEconomico.objects.count(), 1)
        bitacora = Bitacora.objects.get()
        self.assertEqual(bitacora.accion, AccionBitacora.ALTA_MOVIMIENTO_ECONOMICO)
        self.assertEqual(bitacora.tabla_afectada, 'movimiento_economico')
        self.assertEqual(bitacora.usuario, self.propietario)

    def test_registrar_inversion_valida(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(
            URL_LISTA,
            self.payload(
                tipo=TipoMovimientoEconomico.INVERSION,
                categoria=CategoriaMovimientoEconomico.EQUIPOS,
                concepto='Horno rotativo',
                monto='12500.00',
            ),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['tipo_display'], 'Inversión')

    def test_categoria_por_defecto_es_otros(self):
        self.client.force_authenticate(user=self.propietario)
        datos = self.payload()
        datos.pop('categoria')
        res = self.client.post(URL_LISTA, datos, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['categoria'], CategoriaMovimientoEconomico.OTROS)

    def test_monto_cero_rechazado(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(monto='0.00'), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)
        self.assertEqual(Bitacora.objects.count(), 0)

    def test_monto_negativo_rechazado(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(monto='-15.00'), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_monto_con_tres_decimales_rechazado(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(monto='10.123'), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_tipo_invalido_rechazado(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(tipo='sueldo'), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tipo', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_categoria_invalida_rechazada(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(categoria='viajes'), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('categoria', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_concepto_vacio_rechazado(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(URL_LISTA, self.payload(concepto='   '), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('concepto', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_fecha_futura_rechazada(self):
        self.client.force_authenticate(user=self.propietario)
        futura = (timezone.now() + timedelta(days=1)).isoformat()
        res = self.client.post(
            URL_LISTA, self.payload(fecha_hora=futura), format='json'
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_hora', res.data)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_fecha_pasada_se_acepta(self):
        self.client.force_authenticate(user=self.propietario)
        ayer = timezone.now() - timedelta(days=1)
        res = self.client.post(
            URL_LISTA, self.payload(fecha_hora=ayer.isoformat()), format='json'
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        movimiento = MovimientoEconomico.objects.get()
        self.assertEqual(
            timezone.localtime(movimiento.fecha_hora).date(),
            timezone.localtime(ayer).date(),
        )

    def test_responsable_sale_de_la_sesion_no_del_payload(self):
        """Aunque el cliente envíe id_usuario, se ignora y manda la sesión."""
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(
            URL_LISTA, self.payload(id_usuario=self.sin_permiso.pk), format='json'
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        movimiento = MovimientoEconomico.objects.get()
        self.assertEqual(movimiento.id_usuario, self.propietario)

    def test_sin_permiso_devuelve_403(self):
        self.client.force_authenticate(user=self.sin_permiso)
        res = self.client.post(URL_LISTA, self.payload(), format='json')

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_sin_autenticacion_devuelve_401(self):
        res = self.client.post(URL_LISTA, self.payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)

    def test_falla_bitacora_revierte_el_movimiento(self):
        """Si la auditoría falla, el gasto tampoco se guarda (atomic)."""
        self.client.force_authenticate(user=self.propietario)
        with patch(
            'apps.compras.gastos.services.registrar_movimiento.Bitacora.registrar',
            side_effect=DjangoValidationError({'detail': 'Bitácora no disponible'}),
        ):
            res = self.client.post(URL_LISTA, self.payload(), format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MovimientoEconomico.objects.count(), 0)
        self.assertEqual(Bitacora.objects.count(), 0)

    def test_base_de_datos_rechaza_monto_no_positivo(self):
        """El CHECK es real: no depende solo del serializer."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_movimiento(monto='0.00')

    def test_base_de_datos_rechaza_tipo_invalido(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_movimiento(tipo='sueldo')

    def test_base_de_datos_rechaza_categoria_invalida(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_movimiento(categoria='viajes')

    def test_servicio_rechaza_fecha_futura_sin_zona_horaria(self):
        """El servicio también protege cuando lo llama código interno (naive)."""
        with self.assertRaises(DjangoValidationError):
            registrar_movimiento(
                usuario=self.propietario,
                tipo=TipoMovimientoEconomico.GASTO,
                concepto='Pago adelantado',
                monto='5.00',
                fecha_hora=datetime.now() + timedelta(days=2),
            )
        self.assertEqual(MovimientoEconomico.objects.count(), 0)


class PruebasListadoGastos(BasePruebasGastos):
    def setUp(self):
        super().setUp()
        ahora = timezone.now()
        self.gasto_servicios = self.crear_movimiento(
            concepto='Energía eléctrica',
            categoria=CategoriaMovimientoEconomico.SERVICIOS,
            tipo=TipoMovimientoEconomico.GASTO,
            fecha_hora=ahora - timedelta(days=10),
        )
        self.inversion_equipos = self.crear_movimiento(
            concepto='Amasadora industrial',
            categoria=CategoriaMovimientoEconomico.EQUIPOS,
            tipo=TipoMovimientoEconomico.INVERSION,
            fecha_hora=ahora - timedelta(days=2),
        )

    def test_listado_ordenado_por_fecha_descendente(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(URL_LISTA)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [fila['id_movimiento'] for fila in res.data]
        self.assertEqual(ids, [self.inversion_equipos.pk, self.gasto_servicios.pk])

    def test_filtra_por_tipo_y_categoria(self):
        self.client.force_authenticate(user=self.propietario)

        res_tipo = self.client.get(URL_LISTA, {'tipo': 'inversion'})
        self.assertEqual(len(res_tipo.data), 1)
        self.assertEqual(res_tipo.data[0]['id_movimiento'], self.inversion_equipos.pk)

        res_categoria = self.client.get(URL_LISTA, {'categoria': 'servicios'})
        self.assertEqual(len(res_categoria.data), 1)
        self.assertEqual(res_categoria.data[0]['id_movimiento'], self.gasto_servicios.pk)

    def test_filtra_por_rango_de_fechas(self):
        self.client.force_authenticate(user=self.propietario)
        desde = (timezone.now() - timedelta(days=5)).date().isoformat()
        hasta = timezone.now().date().isoformat()

        res = self.client.get(URL_LISTA, {'fecha_desde': desde, 'fecha_hasta': hasta})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id_movimiento'], self.inversion_equipos.pk)

    def test_filtro_por_texto(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(URL_LISTA, {'search': 'amasadora'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id_movimiento'], self.inversion_equipos.pk)

    def test_fecha_desde_mayor_que_fecha_hasta_es_error(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(
            URL_LISTA,
            {'fecha_desde': '2026-11-10', 'fecha_hasta': '2026-11-01'},
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_desde', res.data)

    def test_anulado_invalido_es_error(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(URL_LISTA, {'anulado': 'tal_vez'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('anulado', res.data)

    def test_listado_excluye_anulados_por_defecto(self):
        self.client.force_authenticate(user=self.propietario)
        self.gasto_servicios.anulado = True
        self.gasto_servicios.save(update_fields=['anulado'])

        por_defecto = self.client.get(URL_LISTA)
        self.assertEqual(len(por_defecto.data), 1)
        self.assertEqual(por_defecto.data[0]['id_movimiento'], self.inversion_equipos.pk)

        todos = self.client.get(URL_LISTA, {'anulado': 'todos'})
        self.assertEqual(len(todos.data), 2)

        solo_anulados = self.client.get(URL_LISTA, {'anulado': 'true'})
        self.assertEqual(len(solo_anulados.data), 1)
        self.assertEqual(solo_anulados.data[0]['id_movimiento'], self.gasto_servicios.pk)


class PruebasDetalleYAnulacion(BasePruebasGastos):
    def setUp(self):
        super().setUp()
        self.movimiento = self.crear_movimiento()

    def test_detalle_devuelve_el_movimiento(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(f'{URL_LISTA}{self.movimiento.pk}/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id_movimiento'], self.movimiento.pk)
        self.assertEqual(res.data['concepto'], 'Energía eléctrica')

    def test_detalle_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(f'{URL_LISTA}999999/')

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_anular_marca_el_movimiento_y_registra_bitacora(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(f'{URL_LISTA}{self.movimiento.pk}/anular/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['anulado'])

        self.movimiento.refresh_from_db()
        self.assertTrue(self.movimiento.anulado)
        # Sigue existiendo: anular no borra.
        self.assertTrue(
            MovimientoEconomico.objects.filter(pk=self.movimiento.pk).exists()
        )

        bitacora = Bitacora.objects.get(
            accion=AccionBitacora.ANULACION_MOVIMIENTO_ECONOMICO
        )
        self.assertEqual(bitacora.tabla_afectada, 'movimiento_economico')
        self.assertEqual(bitacora.usuario, self.propietario)

    def test_anular_movimiento_con_motivo_queda_en_bitacora(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(
            f'{URL_LISTA}{self.movimiento.pk}/anular/',
            {'motivo': 'Error en digitación de monto'},
            format='json',
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['anulado'])

        bitacora = Bitacora.objects.get(
            accion=AccionBitacora.ANULACION_MOVIMIENTO_ECONOMICO
        )
        self.assertIn('Error en digitación de monto', bitacora.descripcion)

    def test_listado_con_paginacion_opcional(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.get(f'{URL_LISTA}?page=1&page_size=5')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('count', res.data)
        self.assertIn('results', res.data)

    def test_doble_anulacion_devuelve_400(self):
        self.client.force_authenticate(user=self.propietario)
        primero = self.client.post(f'{URL_LISTA}{self.movimiento.pk}/anular/')
        segundo = self.client.post(f'{URL_LISTA}{self.movimiento.pk}/anular/')

        self.assertEqual(primero.status_code, status.HTTP_200_OK)
        self.assertEqual(segundo.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', segundo.data)
        self.assertEqual(
            Bitacora.objects.filter(
                accion=AccionBitacora.ANULACION_MOVIMIENTO_ECONOMICO
            ).count(),
            1,
        )

    def test_anular_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.propietario)
        res = self.client.post(f'{URL_LISTA}999999/anular/')

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_anular_sin_permiso_devuelve_403(self):
        self.client.force_authenticate(user=self.sin_permiso)
        res = self.client.post(f'{URL_LISTA}{self.movimiento.pk}/anular/')

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.movimiento.refresh_from_db()
        self.assertFalse(self.movimiento.anulado)
