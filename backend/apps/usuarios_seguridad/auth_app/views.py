from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.usuarios_seguridad.auth_app.serializers import (
    RECUPERACION_ENVIADA,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    RecuperacionConfirmacionSerializer,
    RecuperacionSolicitudSerializer,
    UsuarioProfileSerializer,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


class LoginThrottle(AnonRateThrottle):
    """
    Límite de peticiones por IP sobre el endpoint de login.

    Complementa, y no reemplaza, al bloqueo por cuenta: aquel protege una
    cuenta concreta, este frena al atacante que recorre cientos de cuentas
    distintas desde una sola IP.
    """

    scope = 'login'


class CustomLoginView(TokenObtainPairView):
    """
    Vista de Login (CU1).

    Es deliberadamente fina: no reimplementa el flujo. Toda la lógica de
    negocio (bloqueo, conteo de intentos, auditoría y emisión de tokens) está en
    `CustomTokenObtainPairSerializer` y en `auth_app.services.politica_bloqueo`.

    La versión anterior sobrescribía `post()` y, para conocer al usuario que
    había iniciado sesión, volvía a ejecutar la validación completa del
    serializador: una segunda consulta de usuario y una segunda verificación de
    contraseña en cada login exitoso. Ese costo se eliminó al mover la
    auditoría al serializador, que ya conoce al usuario.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]
    throttle_scope = 'login'


class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista para refrescar el access token a partir de un refresh token válido.

    Se le da el scope 'refresh' y no el de 'login': el rate 'refresh' ya estaba
    declarado en settings.py y nunca se aplicaba, porque el scope equivocado
    hacía que este endpoint consumiera el cupo del login. Era inofensivo
    (10/min alcanzaba para refrescar) pero dejaba la tabla de rates con una
    entrada muerta y hacía creer que el refresco estaba más protegido de lo que
    estaba.
    """

    throttle_classes = [LoginThrottle]
    throttle_scope = 'refresh'

class UserProfileView(APIView):
    """
    Endpoint /api/auth/me/
    Retorna la información del usuario autenticado en la sesión activa.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==================================================================
# CU2 — Recuperar contraseña
# ==================================================================


class RecuperacionSolicitudThrottle(AnonRateThrottle):
    """
    Límite por IP sobre la solicitud del enlace.

    Es la capa que frena el BARRIDO: un atacante con una IP que pide cien enlaces
    en un minuto para cien correos distintos. La política por cuenta, que vive en
    `recuperacion.services.token.evaluar_solicitud`, es la otra capa y frena lo
    contrario: el ataque dirigido a una sola cuenta desde IPs que van rotando.
    Juntas se cubren; por separado dejan un hueco.
    """

    scope = 'password_reset_request'


class RecuperacionConfirmacionThrottle(AnonRateThrottle):
    """Límite por IP sobre la confirmación, más alto porque el token ya es un secreto."""

    scope = 'password_reset_confirm'


class RecuperacionSolicitudView(APIView):
    """
    Endpoint /api/auth/password-reset-request/ (CU2, paso 1).

    Devuelve SIEMPRE 200 con el mismo mensaje. La vista es deliberadamente fina:
    no sabe si el correo se envió, solo recibe el resultado booleano del
    serializador para no exponerlo.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [RecuperacionSolicitudThrottle]
    throttle_scope = 'password_reset_request'
    serializer_class = RecuperacionSolicitudSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': RECUPERACION_ENVIADA},
            status=status.HTTP_200_OK,
        )


class RecuperacionConfirmacionView(APIView):
    """
    Endpoint /api/auth/password-reset-confirm/ (CU2, paso 2).

    Recibe el token que venía en el enlace del correo y la contraseña nueva. No
    necesita sesión: es la única operación de todo el sistema que se ejecuta sin
    estar autenticado, y justamente por eso es la única cuyo `AllowAny` está
    justificado: el token en la URL ES la prueba de que el solicitante es el
    dueño del buzón.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [RecuperacionConfirmacionThrottle]
    throttle_scope = 'password_reset_confirm'
    serializer_class = RecuperacionConfirmacionSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()

        return Response(
            {
                'message': 'Contraseña restablecida correctamente. Ya podés iniciar sesión.',
                'nombre_usuario': resultado['usuario'].nombre_usuario,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Endpoint /api/auth/logout/

    Además de registrar el cierre en bitácora, ahora invalida el refresh token
    entrante. Antes solo escribía en bitácora: el token seguía siendo válido
    durante sus 7 días de vida, así que cerrar sesión no cerraba nada.

    El refresh token es OPCIONAL a propósito. Si el navegador lo perdió, la
    sesión debe poder cerrarse igual; lo que no se puede es dejar de invalidar
    los tokens que sí llegan.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh')

        token_revocado = False
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
                token_revocado = True
            except TokenError:
                # Token vencido, malformado o ya revocado: la sesión del
                # navegador se cierra igual, solo que no había nada que revocar.
                token_revocado = False

        Bitacora.registrar(
            usuario=request.user,
            accion=AccionBitacora.CIERRE_SESION,
            tabla_afectada='usuario',
            descripcion=(
                f'Cierre de sesión manual. Refresh token revocado: {token_revocado}.'
            ),
        )

        return Response(
            {
                'message': 'Sesión cerrada exitosamente.',
                'refresh_token_revocado': token_revocado,
            },
            status=status.HTTP_200_OK,
        )
