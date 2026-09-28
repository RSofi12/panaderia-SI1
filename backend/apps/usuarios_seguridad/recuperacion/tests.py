"""
Pruebas del CU2 — Recuperar contraseña.

Qué se verifica acá, y por qué son estos casos y no otros:

* La ANTI-ENUMERACIÓN es la propiedad más importante del endpoint de solicitud.
  Se prueba que usuario inexistente, cuenta inactiva y cuenta que ya agotó sus
  solicitudes devuelven EXACTAMENTE el mismo cuerpo y el mismo código.
* El ciclo de vida del token: vence, se usa una sola vez, se invalida al pedir
  otro y no se puede reutilizar.
* Que el token en claro nunca se guarde en la base de datos.
* Que el límite por token, por cuenta y por IP se cumplan de verdad.
* Que la contraseña nueva pase la MISMA política de fortaleza que usará el CU3.

Se usa `override_settings(EMAIL_BACKEND=locmem)` para no tocar un SMTP real: el
backend de locmem guarda los mensajes enviados en `django.core.mail.outbox`, que
además permite comprobar que el correo lleva el enlace y no la contraseña.
"""
from datetime import timedelta
from threading import Barrier, Thread
from time import sleep
from unittest import mock, skipUnless

from django.contrib.auth import authenticate
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.usuarios_seguridad.auth_app.exceptions import (
    TokenRecuperacionInvalidoError,
)
from apps.usuarios_seguridad.auth_app.serializers import (
    RecuperacionConfirmacionSerializer,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.configuracion.models import ConfiguracionSeguridad
from apps.usuarios_seguridad.recuperacion.models import (
    ALFABETO_TOKEN,
    LONGITUD_TOKEN,
    TokenRecuperacion,
)
from apps.usuarios_seguridad.recuperacion.services import confirmacion
from apps.usuarios_seguridad.recuperacion.services import token as servicio_token
from apps.usuarios_seguridad.users.models import Usuario

CONTRASENA_VALIDA = 'PanADERIA2026!'
CONTRASENA_NUEVA = 'NuevaClave2026!'

# Token de ejemplo para las pruebas que no necesitan que venga de un correo.
# Cualquier valor de 20 caracteres sirve: lo que importa es el hash que se guarda.
TOKEN_VALIDO = 'ABCD2345EFGH6789IJKL'

# Solo le falta la mayúscula: hace fallar el `ComplexPasswordValidator` del
# proyecto y a ningún otro, así que el único mensaje que vuelve es el que está
# escrito a mano en `users/password_validators.py`. Con una contraseña
# demasiado corta fallarían también los validadores de Django, cuyos textos
# dependen de las traducciones instaladas y no son deterministas.
CONTRASENA_SIN_MAYUSCULA = 'panaderia2026!'

# El backend de locmem acumula los correos en memoria en vez de enviarlos por
# SMTP. Es el mismo mecanismo que usa Django en su propia suite de pruebas.
EMAIL_DE_MEMORIA = 'django.core.mail.backends.locmem.EmailBackend'

URL_FRONTEND = 'http://localhost:5173/recuperar-password/nueva'


def envejecer_token(fila, minutos=5):
    """
    Envejece un token hacia el pasado de forma que la base acepte el cambio.

    No basta con restarle minutos a `expira_en`: la tabla tiene un CHECK que
    exige `expira_en > creado_en`, así que hay que retrasar las DOS marcas de
    tiempo. Se usa `update()` para saltarse los validadores del modelo a
    propósito: acá no estamos probando el modelo, estamos fabricando un estado
    que en producción llega solo con el reloj.
    """
    ahora = timezone.now()
    TokenRecuperacion.objects.filter(pk=fila.pk).update(
        creado_en=ahora - timedelta(minutes=minutos + 1),
        expira_en=ahora - timedelta(minutes=minutos),
    )
    fila.refresh_from_db()
    return fila



@override_settings(
    EMAIL_BACKEND=EMAIL_DE_MEMORIA,
    PASSWORD_RESET_URL=URL_FRONTEND,
)
class BasePruebaCU2(TestCase):
    """Arranque común: un usuario con correo y los dos endpoints resueltos."""

    def setUp(self):
        # El cache es el estado que usan los throttles de DRF. Sin limpiarlo, el
        # cupo de una prueba se heredaría a la siguiente y los resultados
        # dependerían del orden de ejecución.
        cache.clear()
        mail.outbox = []

        self.usuario = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password=CONTRASENA_VALIDA,
            nombre_completo='María Elena Gonzales Pérez',
            email='gonzales.ventas@mail.com',
        )

        self.cliente = APIClient()
        self.url_solicitud = reverse('auth_app:password_reset_request')
        self.url_confirmacion = reverse('auth_app:password_reset_confirm')

    def pedir_recuperacion(self, identificador):
        return self.cliente.post(
            self.url_solicitud,
            {'identificador': identificador},
            format='json',
        )

    def confirmar(self, token, contrasena=CONTRASENA_NUEVA, confirmar=None):
        return self.cliente.post(
            self.url_confirmacion,
            {
                'token': token,
                'nueva_contrasena': contrasena,
                'confirmar_contrasena': confirmar if confirmar is not None else contrasena,
            },
            format='json',
        )

    def token_del_ultimo_correo(self):
        """Extrae el token del enlace enviado en el primer correo de outbox."""
        self.assertTrue(mail.outbox, 'No se envió ningún correo')
        cuerpo = mail.outbox[0].body
        prefijo = 'nueva?token='
        inicio = cuerpo.index(prefijo) + len(prefijo)
        return cuerpo[inicio:cuerpo.index('\n', inicio)].strip()


class PruebasSolicitudExitosa(BasePruebaCU2):
    """Caso feliz del paso 1."""

    def test_solicita_por_nombre_de_usuario(self):
        respuesta = self.pedir_recuperacion('vendedor')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['gonzales.ventas@mail.com'])

    def test_solicita_por_correo(self):
        respuesta = self.pedir_recuperacion('gonzales.ventas@mail.com')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_el_correo_se_busca_sin_importar_las_mayusculas(self):
        respuesta = self.pedir_recuperacion('Gonzales.Ventas@Mail.com')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_el_correo_lleva_texto_plano_y_html(self):
        self.pedir_recuperacion('vendedor')

        mensaje = mail.outbox[0]
        self.assertEqual(len(mensaje.alternatives), 1)
        # alternatives es una lista de tuplas (contenido, tipo_mime)
        contenido_html, tipo = mensaje.alternatives[0]
        self.assertEqual(tipo, 'text/html')
        self.assertIn(f'{URL_FRONTEND}?token=', mensaje.body)
        self.assertIn(f'{URL_FRONTEND}?token=', contenido_html)

    def test_el_correo_nunca_lleva_la_contrasena(self):
        """El correo jamás puede contener la contraseña: solo el enlace."""
        self.pedir_recuperacion('vendedor')

        contenido = mail.outbox[0].body + mail.outbox[0].alternatives[0][0]
        self.assertNotIn(CONTRASENA_VALIDA, contenido)
        self.assertIn('restablecer', contenido.lower())

    def test_registra_la_solicitud_en_bitacora(self):
        self.pedir_recuperacion('vendedor')

        registros = Bitacora.objects.filter(accion=AccionBitacora.SOLICITUD_RECUPERACION)
        self.assertEqual(registros.count(), 1)
        self.assertEqual(registros.first().usuario, self.usuario)


class PruebasAntiEnumeracion(BasePruebaCU2):
    """
    La respuesta NO puede revelar si la cuenta existe. Es el requisito central del
    CU2 y el que se rompería con un solo `if usuario is None: return 404`.
    """

    def test_mensaje_identico_entre_cuenta_existente_e_inexistente(self):
        con_cuenta = self.pedir_recuperacion('vendedor')
        mail.outbox = []
        sin_cuenta = self.pedir_recuperacion('no-existe-este-usuario')

        self.assertEqual(con_cuenta.status_code, sin_cuenta.status_code)
        self.assertEqual(con_cuenta.json(), sin_cuenta.json())

    def test_mensaje_identico_para_cuenta_inactiva(self):
        self.usuario.activo = False
        self.usuario.save()

        inactivo = self.pedir_recuperacion('vendedor')
        mail.outbox = []
        inexistente = self.pedir_recuperacion('usuario-fantasma')

        self.assertEqual(inactivo.status_code, inexistente.status_code)
        self.assertEqual(inactivo.json(), inexistente.json())
        # Y además a una cuenta desactivada no se le manda nada.
        self.assertEqual(len(mail.outbox), 0)

    def test_la_bitacora_si_distingue_los_casos(self):
        """Por fuera idéntico; por dentro el Administrador sí puede auditar."""
        self.pedir_recuperacion('usuario-fantasma')
        self.pedir_recuperacion('vendedor')

        registros = Bitacora.objects.filter(
            accion=AccionBitacora.SOLICITUD_RECUPERACION
        ).order_by('id_bitacora')

        self.assertIsNone(registros[0].usuario_id)
        self.assertEqual(registros[0].nombre_usuario_intento, 'usuario-fantasma')
        self.assertEqual(registros[1].usuario_id, self.usuario.id_usuario)

    def test_identificador_vacio_no_dispara_ningun_envio(self):
        """La falta de dato del formulario no es información sobre una cuenta."""
        respuesta = self.pedir_recuperacion('')

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(TokenRecuperacion.objects.count(), 0)


class PruebasAlmacenamientoDelToken(BasePruebaCU2):
    """El token en claro no existe nunca dentro de la base de datos."""

    def test_guarda_solo_el_hash(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        fila = TokenRecuperacion.objects.get(usuario=self.usuario)
        self.assertNotEqual(fila.token_hash, token)
        self.assertEqual(fila.token_hash, TokenRecuperacion.hashear_token(token))
        self.assertEqual(len(fila.token_hash), 64)

    def test_no_se_puede_buscar_por_el_token_en_claro(self):
        """La columna es el hash: una consulta por el valor en claro no acierta."""
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        self.assertFalse(TokenRecuperacion.objects.filter(token_hash=token).exists())
        self.assertTrue(
            TokenRecuperacion.objects.filter(
                token_hash=TokenRecuperacion.hashear_token(token)
            ).exists()
        )

    def test_token_tiene_la_longitud_acordada(self):
        self.assertEqual(LONGITUD_TOKEN, 20)
        self.assertEqual(len(TokenRecuperacion.generar_token()), LONGITUD_TOKEN)

    def test_los_tokens_son_distintos(self):
        self.assertNotEqual(
            TokenRecuperacion.generar_token(),
            TokenRecuperacion.generar_token(),
        )

    def test_el_alfabeto_excluye_los_caracteres_ambiguos(self):
        """
        0/O y 1/I/l se confunden en un correo, y algunos clientes reconstruyen o
        recortan el enlace al previsualizarlo. Excluirlos evita que un token
        válido deje de funcionar por un cambio de tipografía.
        """
        for ambiguo in ('0', '1', 'I', 'O', 'l'):
            with self.subTest(caracter=ambiguo):
                self.assertNotIn(ambiguo, ALFABETO_TOKEN)

        for _ in range(50):
            token = TokenRecuperacion.generar_token()
            for ambiguo in ('0', '1', 'I', 'O', 'l'):
                self.assertNotIn(ambiguo, token)


class PruebasCicloDeVidaDelToken(BasePruebaCU2):
    """Expiración, un solo uso y cancelación al pedir un enlace nuevo."""

    def test_el_token_hereda_el_plazo_de_la_configuracion(self):
        config = ConfiguracionSeguridad.cargar()
        config.minutos_expiracion_token = 15
        config.save()

        self.pedir_recuperacion('vendedor')
        fila = TokenRecuperacion.objects.get(usuario=self.usuario)

        self.assertAlmostEqual(
            (fila.expira_en - fila.creado_en).total_seconds(),
            15 * 60,
            delta=5,
        )
        self.assertTrue(fila.es_valido(config.max_intentos_token))
        self.assertFalse(fila.esta_expirado)

    def test_confirmar_con_token_vencido_falla_sin_tocar_la_contrasena(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()
        envejecer_token(TokenRecuperacion.objects.get(usuario=self.usuario))

        respuesta = self.confirmar(token)

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('ya no es válido', respuesta.json()['error'])
        self.assertTrue(authenticate(username='vendedor', password=CONTRASENA_VALIDA))

    def test_el_token_es_de_un_solo_uso(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        primera = self.confirmar(token)
        segunda = self.confirmar(token)

        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 400)
        self.assertIn('ya no es válido', segunda.json()['error'])

    def test_el_token_se_consume_al_usarlo(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        self.confirmar(token)

        fila = TokenRecuperacion.objects.get(usuario=self.usuario)
        self.assertIsNotNone(fila.usado_en)
        self.assertTrue(fila.esta_usado)

    def test_pedir_otro_enlace_invalida_el_anterior(self):
        self.pedir_recuperacion('vendedor')
        primer_token = self.token_del_ultimo_correo()
        mail.outbox = []

        self.pedir_recuperacion('vendedor')
        segundo_token = self.token_del_ultimo_correo()

        self.assertNotEqual(primer_token, segundo_token)
        # El primero ya no sirve, aunque todavía no haya expirado.
        self.assertEqual(self.confirmar(primer_token).status_code, 400)
        self.assertEqual(self.confirmar(segundo_token).status_code, 200)

    def test_cancelado_no_registrado_como_usado(self):
        """La base de datos no miente: cancelado y usado son cosas distintas."""
        self.pedir_recuperacion('vendedor')
        self.pedir_recuperacion('vendedor')

        fila = TokenRecuperacion.objects.order_by('id_token').first()
        self.assertIsNone(fila.usado_en)
        self.assertIsNotNone(fila.invalidado_en)

    def test_token_inexistente_da_el_mismo_mensaje_que_uno_vencido(self):
        """Sin oráculo: no se puede usar el mensaje para adivinar nada."""
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()
        envejecer_token(TokenRecuperacion.objects.get(usuario=self.usuario))

        vencido = self.confirmar(token)
        inexistente = self.confirmar('ZZZZZZZZZZZZZZZZZZZZ')

        self.assertEqual(vencido.status_code, inexistente.status_code)
        self.assertEqual(vencido.json(), inexistente.json())

    def test_el_rechazo_queda_auditado(self):
        self.confirmar('ZZZZZZZZZZZZZZZZZZZZ')

        registros = Bitacora.objects.filter(accion=AccionBitacora.RECUPERACION_INVALIDADA)
        self.assertEqual(registros.count(), 1)
        self.assertIn('no corresponde a ningún token', registros.first().descripcion)


class PruebasConfirmacionExitosa(BasePruebaCU2):
    """Caso feliz del paso 2 y sus efectos colaterales."""

    def test_confirma_con_token_valido(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        respuesta = self.confirmar(token)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('restablecida', respuesta.json()['message'])
        self.assertEqual(respuesta.json()['nombre_usuario'], 'vendedor')

    def test_cambia_la_contrasena(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        self.confirmar(token)

        self.assertTrue(authenticate(username='vendedor', password=CONTRASENA_NUEVA))
        self.assertFalse(authenticate(username='vendedor', password=CONTRASENA_VALIDA))

    def test_registra_la_confirmacion_en_bitacora(self):
        self.pedir_recuperacion('vendedor')
        self.confirmar(self.token_del_ultimo_correo())

        registros = Bitacora.objects.filter(accion=AccionBitacora.RECUPERACION_CONFIRMADA)
        self.assertEqual(registros.count(), 1)
        self.assertEqual(registros.first().usuario, self.usuario)

    def test_el_token_queda_usado_dentro_de_la_misma_transaccion(self):
        """
        Tras confirmar, el token debe quedar marcado como usado Y con la
        contraseña ya cambiada, sin que ninguna de las dos cosas se haya aplicado
        por separado.

        OJO sobre lo que esta prueba NO cubre: no verifica el lock. Comprobarlo
        exigiría una segunda conexión de base de datos compitiendo, y en SQLite
        en memoria eso daría un falso positivo. Ese caso vive ahora en
        `PruebasConcurrenciaReal`, que corre solo sobre PostgreSQL y sí levanta
        dos conexiones reales; y la revisión manual sobre PostgreSQL que faltaba
        quedó hecha (dos confirmaciones simultáneas del mismo enlace → una gana,
        la otra se rechaza y queda auditada).
        """
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        with transaction.atomic():
            serializer = RecuperacionConfirmacionSerializer(
                data={
                    'token': token,
                    'nueva_contrasena': CONTRASENA_NUEVA,
                    'confirmar_contrasena': CONTRASENA_NUEVA,
                },
                context={'request': self._request_falso()},
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)
            serializer.save()

        fila = TokenRecuperacion.objects.get(usuario=self.usuario)
        self.assertIsNotNone(fila.usado_en)
        self.assertTrue(authenticate(username='vendedor', password=CONTRASENA_NUEVA))

    def _request_falso(self):
        from rest_framework.test import APIRequestFactory

        return APIRequestFactory().post('/api/auth/password-reset-confirm/')

    def test_rechaza_contrasena_sin_mayuscula(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        respuesta = self.confirmar(token, contrasena=CONTRASENA_SIN_MAYUSCULA)

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('mayúscula', respuesta.json()['error'])

    def test_rechaza_contrasenas_que_no_coinciden(self):
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        respuesta = self.confirmar(token, confirmar='OtraClave2026!')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('confirmar_contrasena', respuesta.json())

    def test_contrasena_debil_no_consume_intentos_del_token(self):
        """
        Equivocarse al escribir no es un intento de adivinar. El contador existe
        para frenar a quien encontró un enlace y prueba sin parar, no para castigar
        un error de tecleo.
        """
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        self.confirmar(token, contrasena=CONTRASENA_SIN_MAYUSCULA)

        fila = TokenRecuperacion.objects.get(usuario=self.usuario)
        self.assertEqual(fila.intentos, 0)
        self.assertEqual(self.confirmar(token).status_code, 200)

    def test_revoca_las_sesiones_ya_iniciadas(self):
        """
        Si un atacante entró con la contraseña vieja, recuperar la clave tiene que
        sacarlo del sistema, no solo cambiarle la contraseña.
        """
        login = self.cliente.post(
            reverse('auth_app:login'),
            {'nombre_usuario': 'vendedor', 'password': CONTRASENA_VALIDA},
            format='json',
        )
        self.assertEqual(login.status_code, 200)
        refresh = login.json()['refresh']

        self.pedir_recuperacion('vendedor')
        self.confirmar(self.token_del_ultimo_correo())

        reintento = self.cliente.post(
            reverse('auth_app:token_refresh'),
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(reintento.status_code, 401)

    def test_desbloquea_la_cuenta_si_estaba_bloqueada(self):
        """
        Sin esto habría un círculo sin salida: no puede entrar por bloqueo y no
        puede recuperar la clave porque está bloqueada.
        """
        self.usuario.intentos_fallidos = 3
        self.usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.usuario.save()

        self.pedir_recuperacion('vendedor')
        self.confirmar(self.token_del_ultimo_correo())

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 0)
        self.assertIsNone(self.usuario.bloqueado_hasta)
        self.assertTrue(authenticate(username='vendedor', password=CONTRASENA_NUEVA))


class PruebasLimitesPorCuenta(BasePruebaCU2):
    """El candado por cuenta: cuántos enlaces puede pedir la misma persona."""

    def _configurar(self, **campos):
        config = ConfiguracionSeguridad.cargar()
        for campo, valor in campos.items():
            setattr(config, campo, valor)
        config.save()
        return config

    def test_deja_de_enviar_correo_al_superar_las_solicitudes_por_hora(self):
        """
        Agotada la cuota, la respuesta sigue siendo 200 —igual que para una
        cuenta que no existe— pero NO se emite un tercer enlace. La diferencia
        entre "cuenta real sin cuota" y "cuenta inexistente" solo se registra en
        la bitácora; por fuera el cuerpo es indistinguible.
        """
        self._configurar(max_solicitudes_por_hora=2)

        self.assertEqual(self.pedir_recuperacion('vendedor').status_code, 200)
        self.assertEqual(self.pedir_recuperacion('vendedor').status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

        tercera = self.pedir_recuperacion('vendedor')

        self.assertEqual(tercera.status_code, 200)
        self.assertEqual(len(mail.outbox), 2, 'No debía enviar un tercer correo')
        self.assertEqual(TokenRecuperacion.objects.filter(usuario=self.usuario).count(), 2)

    def test_la_respuesta_del_cuota_agotado_no_distingue_de_un_fantasma(self):
        """
        Esta es la prueba que realmente cierra la puerta de enumeración: se pide
        el mismo endpoint con la cuenta real agotada y con un identificador que
        no existe, y ambos cuerpos tienen que ser byte por byte iguales.
        """
        self._configurar(max_solicitudes_por_hora=1)
        self.pedir_recuperacion('vendedor')
        self.pedir_recuperacion('vendedor')  # agota la cuota

        real = self.pedir_recuperacion('vendedor')
        fantasma = self.pedir_recuperacion('no-existe-este-usuario')

        self.assertEqual(real.status_code, fantasma.status_code)
        self.assertEqual(real.json(), fantasma.json())

    def test_la_ventana_se_libera_cumplida_una_hora(self):
        self._configurar(max_solicitudes_por_hora=1)

        self.pedir_recuperacion('vendedor')
        # La segunda ya agota la cuota, así que no se envía correo...
        self.assertEqual(len(mail.outbox), 1)
        self.pedir_recuperacion('vendedor')
        self.assertEqual(len(mail.outbox), 1)

        # Se envelece la primera solicitud: la ventana de una hora ya pasó.
        TokenRecuperacion.objects.filter(usuario=self.usuario).update(
            creado_en=timezone.now() - timedelta(hours=2)
        )

        # Y con la ventana liberada, vuelve a salir un enlace.
        self.assertEqual(self.pedir_recuperacion('vendedor').status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    def test_un_identificador_inventado_no_puede_agotar_el_cuenta_ajena(self):
        """
        El contador se cuenta sobre filas, y un identificador falso no genera
        fila. Por eso no puede agotarle la cuota a una cuenta ajena, que es lo
        que haría un atacante si quisiera llenar el buzón de otra persona.
        """
        self._configurar(max_solicitudes_por_hora=1)

        for numero in range(5):
            with self.subTest(intento=numero):
                respuesta = self.pedir_recuperacion(f'fantasma-{numero}')
                self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(TokenRecuperacion.objects.count(), 0)


class PruebasLimitesPorToken(BasePruebaCU2):
    """El candado por enlace: cuántos intentos admite un mismo token."""

    def _configurar(self, **campos):
        config = ConfiguracionSeguridad.cargar()
        for campo, valor in campos.items():
            setattr(config, campo, valor)
        config.save()
        return config

    def test_una_confirmacion_exitosa_consume_un_intento(self):
        self._configurar(max_intentos_token=3)
        self.pedir_recuperacion('vendedor')
        self.confirmar(self.token_del_ultimo_correo())

        self.assertEqual(TokenRecuperacion.objects.get(usuario=self.usuario).intentos, 1)

    def test_un_enlace_con_el_ultimo_intento_consumido_muerre(self):
        self._configurar(max_intentos_token=1)
        self.pedir_recuperacion('vendedor')
        token = self.token_del_ultimo_correo()

        self.confirmar(token)

        fila = TokenRecuperacion.objects.get(usuario=self.usuario)
        self.assertEqual(fila.intentos, 1)
        self.assertFalse(fila.es_valido(1))
        # Y una segunda confirmación con el mismo enlace ya no entra.
        self.assertEqual(self.confirmar(token).status_code, 400)


class PruebasThrottlingPorIP(BasePruebaCU2):
    """
    La capa de DRF por IP, que frena el BARRIDO de muchas cuentas desde un mismo
    origen. El settings declara 'password_reset_request': '5/min'.
    """

    def test_429_por_ip_al_superar_el_rate(self):
        # No hace falta tocar la cuota por cuenta: `fantasma-N` no existe, y la
        # cuota por cuenta solo se consulta para usuarios reales y activos. Lo que
        # se mide aquí es exclusivamente el límite por IP.
        respuestas = [
            self.pedir_recuperacion(f'fantasma-{numero}') for numero in range(7)
        ]

        self.assertEqual([r.status_code for r in respuestas[:5]], [200] * 5)
        self.assertEqual([r.status_code for r in respuestas[5:]], [429, 429])

    def test_el_throttle_es_una_clase_de_drf_con_el_scope_correcto(self):
        from apps.usuarios_seguridad.auth_app import views as auth_views

        self.assertEqual(
            auth_views.RecuperacionSolicitudThrottle.scope,
            'password_reset_request',
        )
        self.assertEqual(
            auth_views.RecuperacionConfirmacionThrottle.scope,
            'password_reset_confirm',
        )
        # Y los rates existen de verdad en settings; un scope sin rate haría que
        # DRF permite todo sin avisar.
        from django.conf import settings as django_settings

        rates = django_settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
        self.assertIn('password_reset_request', rates)
        self.assertIn('password_reset_confirm', rates)


class PruebasServicioDeTokens(TestCase):
    """
    Pruebas de la capa de servicio, sin HTTP. Es la razón de existir de esa capa:
    estas reglas se verifican sin montar un cliente ni construir una respuesta.
    """

    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='vendedor',
            password=CONTRASENA_VALIDA,
            nombre_completo='María Elena Gonzales Pérez',
            email='gonzales.ventas@mail.com',
        )

    def test_localiza_por_usuario_por_correo_y_por_nada(self):
        self.assertEqual(servicio_token.localizar_usuario('vendedor'), self.usuario)
        self.assertEqual(
            servicio_token.localizar_usuario('gonzales.ventas@mail.com'),
            self.usuario,
        )
        self.assertIsNone(servicio_token.localizar_usuario('nadie'))
        self.assertIsNone(servicio_token.localizar_usuario('   '))
        self.assertIsNone(servicio_token.localizar_usuario(None))

    def test_crear_token_devuelve_el_claro_y_el_hash_corresponde(self):
        token, fila = servicio_token.crear_token(self.usuario, ip='127.0.0.1')

        self.assertEqual(len(token), LONGITUD_TOKEN)
        self.assertEqual(fila.token_hash, TokenRecuperacion.hashear_token(token))
        self.assertEqual(fila.email_destino, 'gonzales.ventas@mail.com')
        self.assertEqual(fila.ip_origen, '127.0.0.1')

    def test_buscar_por_token_reconoce_cada_estado(self):
        """
        Cada estado se prueba sobre un token APARTE. Si se reutilizara el mismo,
        los estados se encadenarían y el orden de las comprobaciones importaría:
        un token usado que además expiró seguiría siendo USADO, no EXPIRADO, y la
        aserción de EXPIRADO nunca llegaría a ejecutarse.
        """
        config = servicio_token.obtener_configuracion()

        token_valido, _ = servicio_token.crear_token(self.usuario)
        _, estado = servicio_token.buscar_por_token(token_valido, config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.OK)

        token_usado, fila_usado = servicio_token.crear_token(self.usuario)
        TokenRecuperacion.objects.filter(pk=fila_usado.pk).update(
            usado_en=timezone.now()
        )
        _, estado = servicio_token.buscar_por_token(token_usado, config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.USADO)

        token_vencido, fila_vencido = servicio_token.crear_token(self.usuario)
        envejecer_token(fila_vencido)
        _, estado = servicio_token.buscar_por_token(token_vencido, config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.EXPIRADO)

        token_agotado, fila_agotado = servicio_token.crear_token(self.usuario)
        TokenRecuperacion.objects.filter(pk=fila_agotado.pk).update(
            intentos=config.max_intentos_token
        )
        _, estado = servicio_token.buscar_por_token(token_agotado, config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.INTENTOS_AGOTADOS)

        _, estado = servicio_token.buscar_por_token('nada', config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.INEXISTENTE)

        _, estado = servicio_token.buscar_por_token(None, config.max_intentos_token)
        self.assertEqual(estado, servicio_token.EstadoToken.INEXISTENTE)

    def test_reclamar_falla_si_el_token_ya_se_uso(self):
        """La segunda reserva del mismo enlace se rechaza: es de un solo uso."""
        config = servicio_token.obtener_configuracion()
        _, fila = servicio_token.crear_token(self.usuario)

        reservada = servicio_token.reclamar_token(fila, config.max_intentos_token)
        self.assertIsNotNone(reservada)
        self.assertEqual(reservada.intentos, 1)

        # Así lo deja aplicar_nueva_contrasena(). Se usa update() y no save()
        # porque `fila` es una copia anterior a la reserva: un save() escribiría
        # de vuelta el `intentos=0` que tenía en memoria.
        TokenRecuperacion.objects.filter(pk=fila.pk).update(
            usado_en=timezone.now()
        )

        self.assertIsNone(servicio_token.reclamar_token(fila, config.max_intentos_token))

    def test_evaluar_solicitud_cuenta_la_ventana(self):
        config = servicio_token.obtener_configuracion()
        config.max_solicitudes_por_hora = 2
        config.save()

        estado = servicio_token.evaluar_solicitud(self.usuario)
        self.assertTrue(estado.permitida)
        self.assertEqual(estado.solicitudes_ultima_hora, 0)
        self.assertEqual(estado.max_por_hora, 2)

        servicio_token.crear_token(self.usuario)
        estado = servicio_token.evaluar_solicitud(self.usuario)
        self.assertTrue(estado.permitida)
        self.assertEqual(estado.solicitudes_ultima_hora, 1)

        servicio_token.crear_token(self.usuario)
        estado = servicio_token.evaluar_solicitud(self.usuario)
        self.assertFalse(estado.permitida)
        self.assertGreater(estado.minutos_para_reintentar, 0)
        self.assertIn('Demasiadas solicitudes', estado.mensaje_limite)

    def test_purgar_vencidos_no_toca_los_vigentes(self):
        """
        El token vigente debe ser de OTRO usuario. Si se crearan los dos para el
        mismo, `crear_token()` invalidaría el primero al emitir el segundo (solo
        hay un enlace vivo por cuenta) y la prueba mediría lo contrario de lo que
        dice: estaría comprobando que la purga respeta un token ya cancelado.
        """
        otro = Usuario.objects.create_user(
            nombre_usuario='otro',
            password=CONTRASENA_VALIDA,
            nombre_completo='Otro Usuario',
            email='otro.ventas@mail.com',
        )
        _, vigente = servicio_token.crear_token(otro)
        _, vencido = servicio_token.crear_token(self.usuario)
        envejecer_token(vencido)

        cancelados = confirmacion.purgar_vencidos()

        self.assertEqual(cancelados, 1)
        vigente.refresh_from_db()
        vencido.refresh_from_db()
        self.assertIsNone(vigente.invalidado_en)
        self.assertIsNotNone(vencido.invalidado_en)

    def test_el_user_agent_se_trunca(self):
        """Igual que en la bitácora: no depender de una columna tan angosta."""
        _, fila = servicio_token.crear_token(self.usuario, agente='X' * 900)
        self.assertEqual(len(fila.agente_usuario), 255)


class PruebasConfiguracionCU2(TestCase):
    """Los tres parámetros nuevos respetan sus rangos y el singleton sigue igual."""

    def setUp(self):
        self.config = ConfiguracionSeguridad.cargar()

    def test_valores_por_defecto(self):
        self.assertEqual(self.config.minutos_expiracion_token, 15)
        self.assertEqual(self.config.max_intentos_token, 5)
        self.assertEqual(self.config.max_solicitudes_por_hora, 3)

    def test_cada_rango_se_valida(self):
        for campo in ('minutos_expiracion_token', 'max_intentos_token',
                      'max_solicitudes_por_hora'):
            for valor in (0, 5000):
                with self.subTest(campo=campo, valor=valor):
                    config = ConfiguracionSeguridad.cargar()
                    setattr(config, campo, valor)
                    with self.assertRaises(ValidationError):
                        config.clean()

    def test_sigue_siendo_singleton(self):
        self.assertEqual(ConfiguracionSeguridad.cargar().id_configuracion, 1)


class PruebasVocabularioBitacora(TestCase):
    """
    Las acciones de CU2 deben ser valores ADMITIDOS del enum, no cadenas sueltas:
    una errata crearía una categoría nueva y el reporte de CU26 la dejaría fuera.
    """

    def test_acciones_de_recuperacion_existen(self):
        for clave in ('SOLICITUD_RECUPERACION', 'RECUPERACION_CONFIRMADA',
                      'RECUPERACION_INVALIDADA'):
            with self.subTest(clave=clave):
                self.assertEqual(AccionBitacora[clave].value, clave)

    def test_vocabulario_original_intacto(self):
        for clave in ('INICIO_SESION', 'LOGIN_FALLIDO', 'ACCESO_BLOQUEADO',
                      'ACCESO_DENEGADO', 'CIERRE_SESION', 'DESBLOQUEO_CUENTA'):
            with self.subTest(clave=clave):
                self.assertEqual(AccionBitacora[clave].value, clave)

    def test_una_accion_inexistente_sigue_fallando(self):
        with self.assertRaises(KeyError):
            AccionBitacora['RECUPERACION_INICIADA']


class PruebasCorreoDelUsuario(TestCase):
    """`email` pasó a ser obligatorio y único: es el canal de recuperación."""

    def _crear(self, nombre_usuario, correo):
        return Usuario.objects.create_user(
            nombre_usuario=nombre_usuario,
            password=CONTRASENA_VALIDA,
            nombre_completo='Usuario Prueba',
            email=correo,
        )

    def test_no_se_pueden_repetir_correos(self):
        self._crear('uno', 'mismo@mail.com')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._crear('dos', 'mismo@mail.com')

    def test_tampoco_si_solo_cambia_el_renglon_de_las_mayusculas(self):
        """
        La unicidad es sobre `Lower('email')`. Si fuera solo sobre `email`,
        'Persona@mail.com' y 'persona@mail.com' serían dos cuentas distintas y la
        recuperación de contraseña quedaría ambigua.
        """
        self._crear('uno', 'Persona@mail.com')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._crear('dos', 'persona@mail.com')

    def test_borrar_la_cuenta_arrastra_sus_tokens(self):
        """
        Los enlaces de una cuenta borrada no pueden sobrevivir. Un token huérfano
        apuntando a un usuario inexistente permitiría reiniciar el reloj de un
        enlace viejo que "ya no le sirve de nada a nadie" y que sin embargo
        alguien con el correo todavía tiene.

        OJO: esto ejercita la cascada que aplica el ORM de Django, que borra los
        tokens relacionados en Python antes de emitir el DELETE. La cascada a
        nivel de base (`ON DELETE CASCADE`, migración `recuperacion.0002`) NO se
        verifica aquí, porque SQLite no la impone: se comprobó a mano sobre
        PostgreSQL con un `DELETE` por SQL crudo.
        """
        usuario = self._crear('con_tokens', 'con.tokens@mail.com')
        servicio_token.crear_token(usuario)
        self.assertEqual(TokenRecuperacion.objects.filter(usuario=usuario).count(), 1)

        usuario.delete()

        self.assertEqual(TokenRecuperacion.objects.count(), 0)


class PruebasAuditoriaAnteConflicto(TestCase):
    """
    Lo que pasa cuando el token se pierde la carrera (CU2 + CU26).

    Esta clase NO prueba el candado: eso necesita dos conexiones de verdad y vive
    en `PruebasConcurrenciaReal`. Lo que prueba acá es una consecuencia del
    candado que es igual de importante y que se puede verificar en un solo hilo:
    el rechazo tiene que QUEDAR AUDITADO.

    El detalle que hace relevante este caso: la reserva del token corre dentro de
    un `transaction.atomic` (para mantener el lock) y el rechazo se decide ahí
    adentro. Si el `raise` que comunica el conflicto estuviera DENTRO de ese
    bloque, Django haría rollback y se llevaría por delante el registro de bitácora
    recién escrito. El resultado sería un sistema que bloquea el ataque pero
    borra la evidencia, que es justo lo contrario de lo que pide el CU26.
    """

    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='concurrente',
            password=CONTRASENA_VALIDA,
            nombre_completo='Persona en Conflicto',
            email='concurrente.ventas@mail.com',
        )
        TokenRecuperacion.objects.create(
            usuario=self.usuario,
            token_hash=TokenRecuperacion.hashear_token(TOKEN_VALIDO),
            email_destino=self.usuario.email,
            creado_en=timezone.now(),
            expira_en=timezone.now() + timedelta(minutes=15),
        )

    def _serializer(self):
        from apps.usuarios_seguridad.auth_app.serializers import (
            RecuperacionConfirmacionSerializer,
        )
        return RecuperacionConfirmacionSerializer(data={
            'token': TOKEN_VALIDO,
            'nueva_contrasena': CONTRASENA_NUEVA,
            'confirmar_contrasena': CONTRASENA_NUEVA,
        })

    def test_el_rechazo_por_conflicto_queda_auditado(self):
        """
        `reclamar_token` devuelve None cuando otra confirmación se adelantó. Ese
        rechazo tiene que aparecer en la bitácora igual que cualquier otro.
        """
        with mock.patch.object(
            servicio_token, 'reclamar_token', return_value=None
        ):
            serializer = self._serializer()
            self.assertTrue(serializer.is_valid(), serializer.errors)
            with self.assertRaises(TokenRecuperacionInvalidoError):
                serializer.save()

        registros = Bitacora.objects.filter(
            accion=AccionBitacora.RECUPERACION_INVALIDADA
        )
        self.assertEqual(
            registros.count(), 1,
            'El rechazo por conflicto NO quedo auditado: se perdio el rastro de '
            'un enlace reused dos veces, que es la senal que el Administrador '
            'necesita ver.',
        )
        self.assertEqual(registros.first().usuario, self.usuario)

    def test_la_contrasena_no_se_toca_cuando_el_token_se_pierde_la_carrera(self):
        """El conflicto se resuelve sin escribir nada en la contraseña."""
        with mock.patch.object(
            servicio_token, 'reclamar_token', return_value=None
        ):
            serializer = self._serializer()
            self.assertTrue(serializer.is_valid(), serializer.errors)
            with self.assertRaises(TokenRecuperacionInvalidoError):
                serializer.save()

        self.usuario.refresh_from_db()
        self.assertTrue(
            authenticate(username='concurrente', password=CONTRASENA_VALIDA),
            'La contrasena original no sobrevive al rechazo por conflicto.',
        )
        self.assertFalse(
            authenticate(username='concurrente', password=CONTRASENA_NUEVA)
        )


@skipUnless(
    connection.vendor == 'postgresql',
    'Requiere PostgreSQL: en SQLite no hay dos conexiones compitiendo por el '
    'lock de fila, asi que la prueba daria un falso positivo.',
)
class PruebasConcurrenciaReal(TransactionTestCase):
    """
    El lock de fila, verificado con DOS CONEXIONES DE VERDAD.

    Por que esto NO se puede probar en la suite normal:

    * `TestCase` envuelve cada prueba en una transaccion y comparte la conexion,
      asi que `select_for_update` no compite con nadie y la prueba pasaria siempre.
    * SQLite en memoria abre una conexion distinta por hilo pero no impone
      bloqueos de fila, asi que las dos escrituras se resuelven sin esperar.

    Ademas la carrera se vuelve DETERMINISTA en vez de depender de suerte: se
    inyecta un retardo en el punto exacto que el `atomic` deberia tener cerrado, y
    una barrera obliga a que el segundo hilo llegue durante ese retardo. Con el
    fix, ese segundo hilo se bloquea en el `SELECT ... FOR UPDATE`; sin el fix, los
    dos "ganan" el token.

    En este entorno la suite corre sobre SQLite, asi que esta clase se salta. Para
    ejecutarla hace falta un rol de PostgreSQL con `CREATEDB`:
        python manage.py test apps.usuarios_seguridad.recuperacion.tests.PruebasConcurrenciaReal
    """

    # Un `TransactionTestCase` de verdad: corta el AtomicTestCase de Django y
    # deja que cada hilo use su propia conexion, que es el punto de la prueba.
    RETARDO = 0.35

    def setUp(self):
        super().setUp()
        cache.clear()
        mail.outbox = []
        self.usuario = Usuario.objects.create_user(
            nombre_usuario='carrera',
            password=CONTRASENA_VALIDA,
            nombre_completo='Persona en Carrera',
            email='carrera.ventas@mail.com',
        )
        token, _fila = servicio_token.crear_token(self.usuario)
        self.token = token
        self.clave_1 = 'ContrasanaUno2026!'
        self.clave_2 = 'ContrasanaDos2026!'

    def _confirmar_en_hilo(self, contrasena, barrera, resultados):
        """
        Una confirmación completa en su propio hilo, con su propia conexion.

        `connections['default']` se resuelve DENTRO del hilo a proposito: una
        conexion de psycopg no se puede compartir entre hilos.
        """
        from apps.usuarios_seguridad.auth_app.serializers import (
            RecuperacionConfirmacionSerializer,
        )

        conexion = connections['default']
        try:
            barrera.wait(timeout=20)
            serializer = RecuperacionConfirmacionSerializer(data={
                'token': self.token,
                'nueva_contrasena': contrasena,
                'confirmar_contrasena': contrasena,
            })
            if not serializer.is_valid():
                resultados[contrasena] = ('RECHAZO', str(serializer.errors))
                return
            serializer.save()
            resultados[contrasena] = ('EXITO', '')
        except Exception as exc:  # noqa: BLE001 - aqui el error ES el resultado
            resultados[contrasena] = ('RECHAZO', type(exc).__name__)
        finally:
            conexion.close()

    def test_dos_confirmaciones_del_mismo_enlace_solo_una_gana(self):
        # Retardo inyectado en el punto exacto que el `atomic` exterior protege:
        # entre reservar el token y cambiar la contraseña.
        original = confirmacion.aplicar_nueva_contrasena

        def lento(fila, nueva_contrasena, ip=None, agente=None):
            sleep(self.RETARDO)
            return original(fila, nueva_contrasena, ip=ip, agente=agente)

        barrera = Barrier(2)
        resultados = {}
        with mock.patch.object(
            confirmacion, 'aplicar_nueva_contrasena', lento
        ):
            hilos = [
                Thread(
                    target=self._confirmar_en_hilo,
                    args=(self.clave_1, barrera, resultados),
                ),
                Thread(
                    target=self._confirmar_en_hilo,
                    args=(self.clave_2, barrera, resultados),
                ),
            ]
            for hilo in hilos:
                hilo.start()
            for hilo in hilos:
                hilo.join(timeout=40)
                self.assertFalse(
                    hilo.is_alive(), 'Un hilo quedo colgado: posible deadlock.'
                )

        exitos = [k for k, v in resultados.items() if v[0] == 'EXITO']
        rechazos = [k for k, v in resultados.items() if v[0] == 'RECHAZO']

        self.assertEqual(
            len(exitos), 1,
            f'Se esperaba 1 confirmacion exitosa y hubo {len(exitos)}: el mismo '
            f'enlace se pudo cobrar mas de una vez, o sea que el candado no esta '
            f'cerrando la ventana. Detalle: {resultados}',
        )
        self.assertEqual(len(rechazos), 1, f'Detalle: {resultados}')

        # La contraseña final debe ser la del hilo que ganó, no una mezcla.
        self.usuario.refresh_from_db()
        self.assertTrue(
            self.usuario.check_password(exitos[0]),
            'La contrasena guardada no es la del hilo que gano.',
        )

        # Y el intento perdedor tiene que haber quedado en la bitácora: bloquear
        # el ataque sin registrarlo sería medio trabajo del CU26.
        invalidadas = Bitacora.objects.filter(
            usuario=self.usuario,
            accion=AccionBitacora.RECUPERACION_INVALIDADA,
        )
        self.assertEqual(
            invalidadas.count(), 1,
            'El intento perdedor no quedo auditado.',
        )
        confirmadas = Bitacora.objects.filter(
            usuario=self.usuario,
            accion=AccionBitacora.RECUPERACION_CONFIRMADA,
        )
        self.assertEqual(confirmadas.count(), 1)
