from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.usuarios_seguridad.auth_app.exceptions import (
    ContrasenaDebilError,
    CuentaInactivaError,
    CredencialesInvalidasError,
    DemasiadosIntentosError,
    TokenRecuperacionInvalidoError,
)
from apps.usuarios_seguridad.auth_app.services import politica_bloqueo
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.recuperacion.services import confirmacion, correo
from apps.usuarios_seguridad.recuperacion.services import token as servicio_token
from apps.usuarios_seguridad.users.models import Usuario
from apps.usuarios_seguridad.users.password_validators import validar_contrasena

# Mensaje único para toda falla de credenciales. Distinguir "usuario no existe"
# de "contraseña incorrecta" permitiría enumerar las cuentas del sistema.
CREDENCIALES_INVALIDAS = CredencialesInvalidasError.default_detail

# Mensaje único de la respuesta de "olvidé mi contraseña". Se devuelve idéntico
# exista o no la cuenta, esté activa o no, y tenga o no saldo de solicitudes.
# Cualquier variación aquí convierte la pantalla en un enumerador de usuarios.
# El detalle real de lo que pasó queda solo en la bitácora.
RECUPERACION_ENVIADA = (
    'Si los datos corresponden a una cuenta activa, te enviamos un enlace para '
    'restablecer tu contraseña. Revisá tu correo, incluida la carpeta de spam.'
)

# El identificador vacío sí se distingue: no es información sobre ninguna cuenta,
# es simplemente un formulario mal llenado.
IDENTIFICADOR_VACIO = 'Ingresá tu nombre de usuario o tu correo electrónico.'
def obtener_ip(request):
    """IP real del cliente, respetando el encabezado que agrega un proxy inverso."""
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def obtener_agente_usuario(request):
    """
    User-Agent del cliente.

    Se audita junto a la IP porque juntos distinguen un ataque automatizado de una
    cuenta legítima: una tarjeta robada llega desde una IP distinta cada vez pero
    con el mismo navegador y la misma versión, mientras que un bot que barre
    cuentas cambia de IP y suele tener un User-Agent genérico o ausente.
    """
    if not request:
        return None
    return request.META.get('HTTP_USER_AGENT') or None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador de Login JWT para Panadería Santiago (CU1).

    Orquesta el flujo completo; el cálculo vive en
    `auth_app.services.politica_bloqueo`:

        1. Validación de formato de los campos.
        2. Bloqueo vigente           -> 429 sin tocar la contraseña.
        3. Cuenta inactiva           -> 400 con mensaje explicativo.
        4. authenticate()            -> falla: cuenta intento y se audita.
                                      -> ok:    reinicia contador y se audita.
    """

    username_field = 'nombre_usuario'

    def validate(self, attrs):
        nombre_usuario = (attrs.get('nombre_usuario') or '').strip()
        contrasena = attrs.get('password') or ''

        if not nombre_usuario or not contrasena:
            raise CredencialesInvalidasError(detail={'error': CREDENCIALES_INVALIDAS})

        request = self.context.get('request')
        ip = obtener_ip(request)
        agente = obtener_agente_usuario(request)

        # La búsqueda es 'exact' a propósito: debe coincidir con el criterio que
        # usa ModelBackend al autenticar, o la cuenta quedaría con el contador
        # desincronizado respecto de las verificaciones de contraseña reales.
        usuario = Usuario.objects.filter(nombre_usuario=nombre_usuario).first()

        # --- 1. Bloqueo vigente: se evalúa ANTES de tocar la contraseña ---
        if usuario:
            estado = politica_bloqueo.evaluar_bloqueo(usuario)
            if estado.bloqueado:
                Bitacora.registrar(
                    usuario=usuario,
                    accion=AccionBitacora.ACCESO_BLOQUEADO,
                    tabla_afectada='usuario',
                    descripcion=(
                        f'Intento de acceso rechazado por bloqueo activo. '
                        f'Intentos fallidos: {estado.intentos_fallidos}/{estado.max_intentos}. '
                        f'Reintentar en {estado.minutos_restantes} min. IP: {ip}'
                    ),
                    nombre_usuario_intento=nombre_usuario,
                    agente_usuario=agente,
                )
                raise DemasiadosIntentosError(
                    mensaje=estado.mensaje_bloqueo,
                    retry_after_seconds=estado.segundos_restantes,
                )

            # --- 2. Cuenta desactivada ---
            if not usuario.activo:
                Bitacora.registrar(
                    usuario=usuario,
                    accion=AccionBitacora.ACCESO_DENEGADO,
                    tabla_afectada='usuario',
                    descripcion=(
                        f'Ingreso rechazado: la cuenta está inactiva. IP: {ip}'
                    ),
                    nombre_usuario_intento=nombre_usuario,
                    agente_usuario=agente,
                )
                raise CuentaInactivaError(detail={'error': CuentaInactivaError.default_detail})

        # --- 3. Autenticación real ---
        user = authenticate(
            request=request,
            nombre_usuario=nombre_usuario,
            password=contrasena,
        )

        if not user:
            return self._manejar_intento_fallido(usuario, nombre_usuario, ip, agente)

        # --- 4. Éxito: se reinicia el contador y se registra el acceso ---
        politica_bloqueo.registrar_intento_exitoso(user)

        Bitacora.registrar(
            usuario=user,
            accion=AccionBitacora.INICIO_SESION,
            tabla_afectada='usuario',
            descripcion=f'Inicio de sesión exitoso desde IP: {ip}',
            agente_usuario=agente,
        )

        refresh = self.get_token(user)

        self.user = user
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id_usuario': user.id_usuario,
                'nombre_usuario': user.nombre_usuario,
                'nombre_completo': user.nombre_completo,
                'email': user.email,
                'id_rol': user.id_rol.id_rol if user.id_rol else None,
                'rol': user.rol_nombre,
                'permisos': user.get_permisos_nombres(),
            },
        }

    def _manejar_intento_fallido(self, usuario, nombre_usuario, ip, agente):
        """
        Contabiliza el fallo y decide la respuesta.

        Para un usuario inexistente NO se lleva cuenta: no hay a qué atribuírsela,
        y así un atacante que pruebe nombres inventados no llena la base de datos.
        Ese intento sí queda registrado en bitácora como evento anónimo.
        """
        if usuario is None:
            Bitacora.registrar(
                accion=AccionBitacora.LOGIN_FALLIDO,
                tabla_afectada='usuario',
                descripcion=(
                    f'Ingreso rechazado: el usuario no existe. IP: {ip}'
                ),
                nombre_usuario_intento=nombre_usuario,
                agente_usuario=agente,
            )
            raise CredencialesInvalidasError(detail={'error': CREDENCIALES_INVALIDAS})

        estado = politica_bloqueo.registrar_intento_fallido(usuario)

        Bitacora.registrar(
            usuario=usuario,
            accion=AccionBitacora.LOGIN_FALLIDO,
            tabla_afectada='usuario',
            descripcion=(
                f'Contraseña incorrecta. '
                f'Intentos fallidos: {estado.intentos_fallidos}/{estado.max_intentos}. '
                f'IP: {ip}'
            ),
            nombre_usuario_intento=nombre_usuario,
            agente_usuario=agente,
        )

        if estado.bloqueado:
            raise DemasiadosIntentosError(
                mensaje=estado.mensaje_bloqueo,
                retry_after_seconds=estado.segundos_restantes,
            )

        # El mensaje es idéntico al de usuario inexistente y no revela cuántos
        # intentos quedan: hacerlo confirmaría que la cuenta existe.
        raise CredencialesInvalidasError(detail={'error': CREDENCIALES_INVALIDAS})

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Claims propios: permiten que el frontend sepa el rol y los permisos
        # sin tener que pedir /me/ en cada carga de página.
        token['id_usuario'] = user.id_usuario
        token['nombre_usuario'] = user.nombre_usuario
        token['nombre_completo'] = user.nombre_completo
        token['id_rol'] = user.id_rol.id_rol if user.id_rol else None
        token['rol'] = user.rol_nombre
        token['permisos'] = user.get_permisos_nombres()

        return token


# ==================================================================
# CU2 — Recuperar contraseña
# ==================================================================


class RecuperacionSolicitudSerializer(serializers.Serializer):
    """
    Paso 1 del CU2: el usuario dice quién es y pide un enlace.

    El campo se llama `identificador` y no `email` porque el enunciado acepta
    nombre de usuario o correo, y nombrarlo `email` obligaría al frontend a
    fingir que se pide un correo. No se le impone formato: un identificador mal
    formado tiene que devolver SIEMPRE el mismo mensaje genérico y no un error de
    formato, o el atacante aprende de la respuesta cómo son las cuentas reales.
    El mensaje del campo vacío sí se personaliza, porque "no escribiste nada" no
    dice nada sobre ninguna cuenta.
    """

    identificador = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
        allow_blank=False,
        error_messages={
            'blank': IDENTIFICADOR_VACIO,
            'required': IDENTIFICADOR_VACIO,
        },
    )

    def save(self, **kwargs):
        """
        Genera el enlace y lo envía, o no hace nada. En AMBOS casos no lanza
        excepciones: el mismo código produce la misma respuesta 200.

        Ese es el requisito más importante de este endpoint. Si la respuesta
        fuera distinta para "usuario inexistente" y "usuario existente", el
        atacante podría recorrer el sistema probando correos y armar una lista de
        cuentas válidas sin ningún acceso. Por eso el frontend puede pintar el
        mismo texto en los dos casos y solo el Administrador, que mira la
        bitácora, puede ver qué pasó realmente.
        """
        identificador = self.validated_data['identificador']
        request = self.context.get('request')
        ip = obtener_ip(request)
        agente = obtener_agente_usuario(request)

        usuario = servicio_token.localizar_usuario(identificador)
        correo_enviado = False

        # Tres condiciones y ninguna se comunica: cuenta inexistente, cuenta
        # desactivada y cuenta que ya volvió a pedir demasiados enlaces. La razón
        # está en la bitácora, no en la respuesta.
        if usuario and usuario.activo:
            estado = servicio_token.evaluar_solicitud(usuario)

            if estado.permitida:
                token, fila = servicio_token.crear_token(
                    usuario, ip=ip, agente=agente
                )
                config = servicio_token.obtener_configuracion()
                correo_enviado = correo.enviar_enlace_recuperacion(
                    usuario, token, config.minutos_expiracion_token
                ) > 0
            else:
                # Exceso de solicitudes por cuenta. NO se devuelve 429: se
                # responde exactamente igual que en el caso feliz y en el de
                # cuenta inexistente.
                #
                # Devolver 429 acá sería una puerta trasera para enumerar
                # cuentas. El único caso que llega a esta rama es el de un
                # usuario REAL, así que un 429 confirmaría su existencia. El
                # argumento de que "hacría falta haber enviado correos de verdad
                # para llegar aquí" no alcanza: con max_solicitudes_por_hora=3,
                # al cuarto intento las direcciones reales empiezan a devolver
                # 429 y las inventadas 200, que es exactamente la lista de
                # cuentas válidas que el atacante buscaba.
                #
                # La protección del buzón NO se pierde: la cuota se sigue
                # contando y aquí no se envía nada, así que la bandeja del
                # usuario deja de recibir enlaces. Quien se abuse de verdad se
                # topa igual con el 429 por IP, que depende de la IP del
                # solicitante y no de la existencia de la cuenta.
                confirmacion.auditar_solicitud(
                    usuario, identificador, False, ip=ip, agente=agente
                )
                return False

        confirmacion.auditar_solicitud(
            usuario, identificador, correo_enviado, ip=ip, agente=agente
        )
        return correo_enviado


class RecuperacionConfirmacionSerializer(serializers.Serializer):
    """
    Paso 2 del CU2: el usuario llega desde el enlace del correo y pone la
    contraseña nueva.

    El token NO se compara con `validar()`: se valida contra la base de datos,
    porque las reglas de vigencia (expiración, un solo uso, límite de intentos)
    solo se pueden comprobar contra la fila real, no contra una expresión regular.
    """

    token = serializers.CharField(
        max_length=64,
        trim_whitespace=True,
        allow_blank=False,
    )
    nueva_contrasena = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
        allow_blank=False,
    )
    confirmar_contrasena = serializers.CharField(
        max_length=128,
        write_only=True,
        allow_blank=False,
    )

    def validate(self, attrs):
        if attrs['nueva_contrasena'] != attrs['confirmar_contrasena']:
            raise serializers.ValidationError({
                'confirmar_contrasena': 'Las contraseñas no coinciden.'
            })
        return attrs

    def save(self, **kwargs):
        request = self.context.get('request')
        ip = obtener_ip(request)
        agente = obtener_agente_usuario(request)

        config = servicio_token.obtener_configuracion()
        fila, estado = servicio_token.buscar_por_token(
            self.validated_data['token'],
            config.max_intentos_token,
        )

        if estado != servicio_token.EstadoToken.OK:
            confirmacion.auditar_token_rechazado(fila, estado, ip=ip, agente=agente)
            raise TokenRecuperacionInvalidoError(
                detail={'error': TokenRecuperacionInvalidoError.default_detail}
            )

        # La política de contraseñas se aplica al ESTABLECER la clave, nunca al
        # entrar. Se reutiliza `users.password_validators.validar_contrasena`, que
        # es el mismo gancho que usará el CU3 al crear usuarios, para que las dos
        # pantallas no puedan divergir.
        #
        # Una contraseña débil NO consume intento del token: el riesgo que ese
        # contador frena es que alguien que seldeó un enlace pruebe sin parar, y
        # una contraseña corta no es un intento de adivinar, es un error de
        # tecleo. Cobrarle el enlace al usuario por escribir mal le quitaría la
        # mitad de las recuperaciones.
        errores = validar_contrasena(
            self.validated_data['nueva_contrasena'],
            usuario=fila.usuario,
        )
        if errores:
            confirmacion.auditar_token_rechazado(
                fila, 'contrasena_debil', ip=ip, agente=agente
            )
            raise ContrasenaDebilError(errores)

        # Reserva atómica del token: revalida bajo lock de fila y consume un
        # intento. Si otra confirmación se adelantó, devuelve None y el token ya
        # está quemado: no se toca la contraseña.
        #
        # El `transaction.atomic` de AQUÍ es lo que cierra la carrera, no el que
        # lleva `reclamar_token` por dentro. Ese solo abre su propia transacción
        # y hace commit al retornar, soltando el `SELECT ... FOR UPDATE` ANTES
        # de que se cambie la contraseña: entre ambas llamadas, una segunda
        # petición concurrente todavía encontraría el token válido y también
        # aplicaría su cambio. Anidado aquí, el `atomic` interno se degrada a
        # savepoint y el lock se mantiene hasta el commit del de acá arriba, es
        # decir, hasta que la contraseña ya quedó escrita.
        with transaction.atomic():
            reservada = servicio_token.reclamar_token(fila, config.max_intentos_token)

            if reservada is not None:
                usuario = confirmacion.aplicar_nueva_contrasena(
                    reservada,
                    self.validated_data['nueva_contrasena'],
                    ip=ip,
                    agente=agente,
                )

        # El rechazo por `reservada is None` se resuelve FUERA del `atomic` a
        # propósito, y esto no es un detalle de estilo: si el `raise` estuviera
        # adentro, Django haría rollback de la transacción y se perdería el
        # registro de bitácora que se acaba de escribir, porque un `raise` que
        # sale de un bloque `atomic` descarta TODO lo que se hizo dentro.
        #
        # Consecuencia real de dejarlo adentro: cuando dos personas confirman el
        # mismo enlace a la vez —que es justamente cuando el Administrador más
        # necesita saberlo, porque significa que un enlace se está usando dos
        # veces— el rastro se perdía en silencio. La seguridad seguía funcionando
        # (una de las dos pierde igual), pero el CU26 dejaba de registrar el
        # evento. Verificado con dos conexiones reales de PostgreSQL:
        # `bitácora INVALIDADA = 0` con el raise adentro, `= 1` con el raise
        # afuera.
        if reservada is None:
            confirmacion.auditar_token_rechazado(
                fila, servicio_token.EstadoToken.USADO, ip=ip, agente=agente
            )
            raise TokenRecuperacionInvalidoError(
                detail={'error': TokenRecuperacionInvalidoError.default_detail}
            )

        return {
            'usuario': usuario,
            'intentos_consumidos': reservada.intentos,
            'intentos_restantes': max(0, config.max_intentos_token - reservada.intentos),
        }


class LogoutSerializer(serializers.Serializer):
    """Payload opcional del cierre de sesión."""

    refresh = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class UsuarioProfileSerializer(serializers.ModelSerializer):
    """Serializador para el endpoint /api/auth/me/"""

    id_rol = serializers.IntegerField(source='id_rol.id_rol', read_only=True)
    rol = serializers.CharField(source='rol_nombre', read_only=True)
    permisos = serializers.ListField(source='get_permisos_nombres', read_only=True)
    esta_bloqueado = serializers.BooleanField(source='is_bloqueado', read_only=True)
    minutos_bloqueo_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Usuario
        fields = (
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'email',
            'activo',
            'id_rol',
            'rol',
            'permisos',
            'intentos_fallidos',
            'esta_bloqueado',
            'minutos_bloqueo_restantes',
        )
        read_only_fields = fields
