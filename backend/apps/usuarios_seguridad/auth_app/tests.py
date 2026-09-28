"""
Pruebas del caso de uso CU1 - Iniciar sesión.

Cubren el camino feliz, la enumeración de usuarios, el bloqueo por intentos
fallidos, la expiración del bloqueo, la auditoría de accesos fallidos y la
revocación del refresh token en el logout.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.usuarios_seguridad.auth_app import views as auth_views
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.configuracion.models import ConfiguracionSeguridad

Usuario = get_user_model()

CONTRASENA_VALIDA = 'PanADERIA2026!'
CONTRASENA_INVALIDA = 'Incorrecta123!'

SIN_THROTTLE = {'throttle_classes': []}


class BasePruebaCU1(TestCase):
    CONTRASENA = CONTRASENA_VALIDA

    def setUp(self):
        self.client = APIClient()
        # El login tiene throttling por IP (10/min) y la suite supera ese límite
        # a propósito, así que se desactiva salvo en la clase que lo prueba.
        patcher = patch.multiple(
            auth_views,
            CustomLoginView=SIN_THROTTLE,
            CustomTokenRefreshView=SIN_THROTTLE,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        cache.clear()

        self.usuario = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password=self.CONTRASENA,
            nombre_completo='Vendedor de Prueba',
        )
        self.url_login = reverse('auth_app:login')
        self.url_logout = reverse('auth_app:logout')
        self.url_refresh = reverse('auth_app:token_refresh')
        self.url_perfil = reverse('auth_app:user_profile')

    def intentar_login(self, usuario='vendedor', contrasena=None):
        return self.client.post(
            self.url_login,
            {'nombre_usuario': usuario, 'password': contrasena or self.CONTRASENA},
            format='json',
        )


class PruebasCaminoFeliz(BasePruebaCU1):

    def test_login_exitoso_devuelve_tokens_y_usuario(self):
        respuesta = self.intentar_login()

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)
        self.assertEqual(respuesta.data['user']['nombre_usuario'], 'vendedor')
        self.assertIn('rol', respuesta.data['user'])
        self.assertIn('permisos', respuesta.data['user'])

    def test_login_exitoso_registra_bitacora(self):
        self.intentar_login()

        registro = Bitacora.objects.filter(accion=AccionBitacora.INICIO_SESION).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario, self.usuario)

    def test_perfil_requiere_token(self):
        self.assertEqual(self.client.get(self.url_perfil).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_perfil_devuelve_datos_con_token(self):
        respuesta = self.intentar_login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")

        respuesta = self.client.get(self.url_perfil)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre_usuario'], 'vendedor')

    def test_campos_vacios_son_rechazados(self):
        respuesta = self.client.post(self.url_login, {}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class PruebasAntiEnumeracion(BasePruebaCU1):
    """
    El mensaje de credenciales inválidas debe ser idéntico exista o no el
    usuario: si difiere, un atacante puede listar las cuentas del sistema.
    """

    def test_usuario_inexistente_da_mismo_mensaje_que_contrasena_mala(self):
        inexistente = self.intentar_login(usuario='no_existe', contrasena='loquesea1A!')
        existente = self.intentar_login(usuario='vendedor', contrasena=CONTRASENA_INVALIDA)

        self.assertEqual(inexistente.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(existente.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(inexistente.data['error'], existente.data['error'])

    def test_intento_fallido_no_revela_cuantos_intentos_quedan(self):
        respuesta = self.intentar_login(contrasena=CONTRASENA_INVALIDA)
        self.assertNotIn('intentos', str(respuesta.data).lower())


class PruebasBloqueoPorIntentos(BasePruebaCU1):

    def test_tres_intentos_fallidos_bloquean_la_cuenta(self):
        for _ in range(2):
            respuesta = self.intentar_login(contrasena=CONTRASENA_INVALIDA)
            self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        # El tercero sí alcanza el umbral.
        respuesta = self.intentar_login(contrasena=CONTRASENA_INVALIDA)
        self.assertEqual(respuesta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_bloqueado)
        self.assertEqual(self.usuario.intentos_fallidos, 3)

    def test_cuenta_bloqueada_rechaza_incluso_la_contrasena_correcta(self):
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        respuesta = self.intentar_login(contrasena=self.CONTRASENA)

        self.assertEqual(respuesta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('bloqueada', respuesta.data['error'].lower())

    def test_bloqueo_informa_los_segundos_que_faltan_para_reintentar(self):
        """
        El frontend necesita una cuenta regresiva real. Con la ventana en minutos,
        un bloqueo de 60 s se comunicaría como "1 minuto" aunque quedaran 2.
        """
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        respuesta = self.intentar_login()

        self.assertEqual(respuesta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(respuesta.data['retry_after_seconds'], 10 * 60)

    def test_bloqueo_publica_la_cabecera_retry_after(self):
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        respuesta = self.intentar_login()

        self.assertEqual(respuesta['Retry-After'], str(10 * 60))

    def test_el_tiempo_que_queda_va_decreciendo(self):
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        primero = self.intentar_login().data['retry_after_seconds']

        # Se acorta la ventana a la mitad en lugar de esperar.
        Usuario.objects.filter(pk=self.usuario.pk).update(
            bloqueado_hasta=timezone.now() + timedelta(minutes=5)
        )
        segundo = self.intentar_login().data['retry_after_seconds']

        self.assertGreater(primero, segundo)
        self.assertEqual(segundo, 5 * 60)

    def test_bloqueo_registra_acceso_bloqueado_en_bitacora(self):
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        self.intentar_login(contrasena=self.CONTRASENA)

        self.assertTrue(
            Bitacora.objects.filter(accion=AccionBitacora.ACCESO_BLOQUEADO).exists()
        )

    def test_bloqueo_expira_y_limpia_el_contador(self):
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        # Se simula el paso del tiempo en lugar de esperar 10 minutos.
        Usuario.objects.filter(pk=self.usuario.pk).update(
            bloqueado_hasta=timezone.now() - timedelta(minutes=1)
        )

        respuesta = self.intentar_login()

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_bloqueado)
        self.assertEqual(self.usuario.intentos_fallidos, 0)

    def test_tras_expirar_el_bloqueo_hay_tres_intentos_nuevos(self):
        """
        El ciclo completo de la cuenta bloqueada, que es lo que el usuario vive:

            3 fallos -> bloqueada -> espera la ventana -> 3 intentos NUEVOS -> ...

        Fijar esto con una prueba es lo que garantiza que el desbloqueo automático
        no degrade a "un solo reintento". Si alguien tocara el reinicio del contador
        al limpiar la ventana vencida, esta prueba lo detectaría.
        """
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        # Vence la ventana sin esperar 10 minutos.
        Usuario.objects.filter(pk=self.usuario.pk).update(
            bloqueado_hasta=timezone.now() - timedelta(seconds=1)
        )

        # Ronda 2: los tres intentos deben volver a estar disponibles, uno por uno.
        for intento in range(1, 4):
            respuesta = self.intentar_login(contrasena=CONTRASENA_INVALIDA)
            self.usuario.refresh_from_db()
            self.assertEqual(
                self.usuario.intentos_fallidos,
                intento,
                f'El intento {intento} de la segunda ronda no se conto bien',
            )
            if intento < 3:
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
            else:
                self.assertEqual(
                    respuesta.status_code, status.HTTP_429_TOO_MANY_REQUESTS
                )

        self.assertTrue(self.usuario.is_bloqueado)

    def test_la_ventana_del_bloqueo_usa_el_valor_configurado(self):
        """El administrador cambia los minutos desde la base de datos."""
        config = ConfiguracionSeguridad.cargar()
        config.minutos_bloqueo = 45
        config.save()

        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        respuesta = self.intentar_login()

        self.assertEqual(respuesta.data['retry_after_seconds'], 45 * 60)
        self.assertIn('45 minutos', respuesta.data['error'])

    def test_login_exitoso_reinicia_el_contador(self):
        self.intentar_login(contrasena=CONTRASENA_INVALIDA)
        self.intentar_login(contrasena=CONTRASENA_INVALIDA)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 2)

        self.intentar_login()

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 0)
        self.assertIsNone(self.usuario.bloqueado_hasta)
        self.assertIsNotNone(self.usuario.last_login)

    def test_usuario_inexistente_no_consume_intentos_de_otros(self):
        self.intentar_login(usuario='fantasma', contrasena='loquesea1A!')
        self.intentar_login(usuario='fantasma', contrasena='loquesea1A!')

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 0)

    def test_la_politica_es_configurable_en_la_base_de_datos(self):
        config = ConfiguracionSeguridad.cargar()
        config.max_intentos_fallidos = 1
        config.minutos_bloqueo = 5
        config.save()

        respuesta = self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        self.assertEqual(respuesta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 1)

    def test_ya_bloqueada_un_intento_mas_no_reinicia_la_ventana(self):
        """
        El caso límite del `select_for_update`: si la cuenta ya está bloqueada y
        la ventana sigue vigente, un intento adicional NO debe volver a contar ni
        alargar el bloqueo, solo informa cuánto falta.
        """
        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        Usuario.objects.filter(pk=self.usuario.pk).update(
            bloqueado_hasta=timezone.now() + timedelta(minutes=7)
        )
        original = Usuario.objects.get(pk=self.usuario.pk).bloqueado_hasta

        for _ in range(3):
            self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 3)
        self.assertEqual(self.usuario.bloqueado_hasta, original)


class PruebasCuentaInactiva(BasePruebaCU1):

    def test_cuenta_inactiva_es_rechazada(self):
        self.usuario.activo = False
        self.usuario.save()

        respuesta = self.intentar_login()

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inactiva', respuesta.data['error'].lower())


class PruebasAuditoriaFallos(BasePruebaCU1):
    """
    El hueco más grave que se corrigió: antes, un intento fallido no quedaba
    registrado porque la bitácora exigía un usuario autenticado.
    """

    AGENTE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'

    def test_intento_fallido_con_usuario_existente_queda_auditado(self):
        self.intentar_login(contrasena=CONTRASENA_INVALIDA)

        registro = Bitacora.objects.filter(accion=AccionBitacora.LOGIN_FALLIDO).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.nombre_usuario_intento, 'vendedor')
        self.assertIn('1/3', registro.descripcion)

    def test_intento_fallido_con_usuario_inexistente_queda_auditado_sin_usuario(self):
        self.intentar_login(usuario='fantasma', contrasena='loquesea1A!')

        registro = Bitacora.objects.filter(accion=AccionBitacora.LOGIN_FALLIDO).first()
        self.assertIsNotNone(registro)
        self.assertIsNone(registro.usuario)
        self.assertEqual(registro.nombre_usuario_intento, 'fantasma')

    def test_la_bitacora_guarda_ip_y_navegador(self):
        """
        IP y User-Agent juntos son lo que separa a una persona de un bot que
        barre cuentas: el bot cambia de IP y trae un User-Agent genérico o vacío.
        """
        self.client.post(
            self.url_login,
            {'nombre_usuario': 'vendedor', 'password': CONTRASENA_INVALIDA},
            format='json',
            HTTP_USER_AGENT=self.AGENTE,
        )

        registro = Bitacora.objects.filter(accion=AccionBitacora.LOGIN_FALLIDO).first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.agente_usuario, self.AGENTE)
        self.assertIn('IP:', registro.descripcion)

    def test_un_user_agent_enorme_se_trunca_en_lugar_de_romper_el_registro(self):
        gigante = 'x' * 900

        self.client.post(
            self.url_login,
            {'nombre_usuario': 'vendedor', 'password': CONTRASENA_INVALIDA},
            format='json',
            HTTP_USER_AGENT= gigante,
        )

        registro = Bitacora.objects.filter(accion=AccionBitacora.LOGIN_FALLIDO).first()
        self.assertIsNotNone(registro)
        self.assertEqual(len(registro.agente_usuario), 255)


class PruebasVocabularioBitacora(TestCase):
    """
    El enum debe seguir guardando exactamente el mismo texto que antes, porque los
    reportes ya consultan por esos literales y el DDL los tiene.
    """

    def test_los_valores_del_enum_no_cambiaron(self):
        self.assertEqual(AccionBitacora.INICIO_SESION, 'INICIO_SESION')
        self.assertEqual(AccionBitacora.LOGIN_FALLIDO, 'LOGIN_FALLIDO')
        self.assertEqual(AccionBitacora.ACCESO_BLOQUEADO, 'ACCESO_BLOQUEADO')
        self.assertEqual(AccionBitacora.ACCESO_DENEGADO, 'ACCESO_DENEGADO')
        self.assertEqual(AccionBitacora.CIERRE_SESION, 'CIERRE_SESION')
        self.assertEqual(AccionBitacora.DESBLOQUEO_CUENTA, 'DESBLOQUEO_CUENTA')

    def test_una_accion_inexistente_falla_al_escribirse(self):
        """
        Esta es la razón de usar el enum: una errata ahora lanza KeyError de
        entrada, en vez de crear en silencio una categoría que ningún reporte
        agrupa.
        """
        with self.assertRaises(KeyError):
            AccionBitacora['LOGIN_FALIDO']


class PruebasLogout(BasePruebaCU1):

    def test_logout_revoca_el_refresh_token(self):
        tokens = self.intentar_login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        respuesta = self.client.post(
            self.url_logout, {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertTrue(respuesta.data['refresh_token_revocado'])

        # El refresh token revocado ya no debe servir para obtener un access token.
        self.client.credentials()
        respuesta = self.client.post(
            self.url_refresh, {'refresh': tokens['refresh']}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_sin_refresh_tokenIgualmente_cierra_sesion(self):
        tokens = self.intentar_login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        respuesta = self.client.post(self.url_logout, {}, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.data['refresh_token_revocado'])
        self.assertTrue(
            Bitacora.objects.filter(accion=AccionBitacora.CIERRE_SESION).exists()
        )


class PruebasConfiguracionSeguridad(TestCase):

    def test_la_tabla_admite_una_sola_fila(self):
        ConfiguracionSeguridad.cargar()
        with self.assertRaises(Exception):
            ConfiguracionSeguridad.objects.create(
                id_configuracion=1, max_intentos_fallidos=9, minutos_bloqueo=99
            )

    def test_rangos_fuera_de_limite_son_rechazados(self):
        config = ConfiguracionSeguridad(max_intentos_fallidos=0, minutos_bloqueo=10)
        with self.assertRaises(Exception):
            config.full_clean()


class PruebasThrottlingLogin(TestCase):
    """El límite por IP frena el barrido de cuentas distintas desde una máquina."""

    def setUp(self):
        cache.clear()
        self.url_login = reverse('auth_app:login')

    def test_login_supera_el_limite_por_ip(self):
        # Se sube el umbral de intentos para que la respuesta 429 provenga del
        # throttling por IP y no del bloqueo por cuenta.
        config = ConfiguracionSeguridad.cargar()
        config.max_intentos_fallidos = 20
        config.save()

        Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password=CONTRASENA_VALIDA,
            nombre_completo='Vendedor de Prueba',
        )

        respuestas = [
            APIClient().post(
                self.url_login,
                {'nombre_usuario': 'vendedor', 'password': 'Incorrecta123!'},
                format='json',
            )
            for _ in range(12)
        ]

        self.assertIn(
            status.HTTP_429_TOO_MANY_REQUESTS,
            [r.status_code for r in respuestas],
        )

        # Tras el parche, el bloqueo por cuenta y el throttling por IP comparten el
        # 429. Se distinguen por el cuerpo: solo el bloqueo por cuenta informa
        # `retry_after_seconds`, porque es el único que conoce su propia ventana.
        por_ip = [r for r in respuestas if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertTrue(all('retry_after_seconds' not in r.data for r in por_ip))

    def test_el_429_por_cuenta_informa_los_segundos_que_faltan(self):
        """Contracara del anterior: aquí el 429 sí trae la cuenta regresiva."""
        self.client = APIClient()
        cache.clear()

        Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password=CONTRASENA_VALIDA,
            nombre_completo='Vendedor de Prueba',
        )

        ultima = None
        for _ in range(3):
            ultima = self.client.post(
                self.url_login,
                {'nombre_usuario': 'vendedor', 'password': 'Incorrecta123!'},
                format='json',
            )

        self.assertEqual(ultima.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(ultima.data['retry_after_seconds'], 10 * 60)
        self.assertEqual(ultima['Retry-After'], str(10 * 60))
