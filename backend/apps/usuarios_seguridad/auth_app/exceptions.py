"""
Excepciones propias del proceso de autenticación (CU1).

Por qué NO se usan `serializers.ValidationError` para los errores de login:

`Serializer.run_validation()` envuelve cualquier `ValidationError` con
`as_serializer_error()`, que convierte un detalle de tipo dict en listas:

    {'error': 'Credenciales inválidas.'}   ->   {'error': ['Credenciales inválidas.']}

Es decir, la clave llega al frontend como ARRAY y no como texto, lo que rompe
el contrato `{"error": "<mensaje>"}` que espera el frontend para pintar el
mensaje con setError(). Una `APIException` en cambio viaja intacta por
`exception_handler()`, así que aquí se usa para mantener la respuesta plana y
consistente: todo error de autenticación devuelve `{"error": "..."}`.

Además, el bloqueo de cuenta NO es un error de validación de datos: es un
estado del negocio, y se distingue con **HTTP 429 Too Many Requests** en vez de
un 400 genérico para que el frontend diferencie "te equivocaste" de "estás
bloqueado".

Sobre por qué 429 y no 423 (Locked): 423 pertenece a la familia WebDAV y
describe un recurso bloqueado por una condición del servidor. Aquí lo que se
limita es la TASA de intentos, que es exactamente lo que significa 429. Además
es el estado que un proxy inverso o una librería HTTP genérica ya saben
interpretar, y DRF convierte el atributo `wait` en la cabecera `Retry-After`.
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class ErrorAutenticacion(APIException):
    """Base de los errores del flujo de login. Todos devuelven 400."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'error_autenticacion'


class CredencialesInvalidasError(ErrorAutenticacion):
    default_detail = 'Credenciales inválidas. Verifique su usuario y contraseña.'
    default_code = 'credenciales_invalidas'


class CuentaInactivaError(ErrorAutenticacion):
    default_detail = 'Esta cuenta de usuario se encuentra inactiva. Contacte al administrador.'
    default_code = 'cuenta_inactiva'


class DemasiadosIntentosError(APIException):
    """
    La cuenta alcanzó el máximo de intentos fallidos y sigue en ventana de bloqueo.

    Se cambió el nombre desde `CuentaBloqueadaError` porque el código HTTP 423
    que usaba antes(resultado de una revisión equivocada) no correspondía con un
    límite de intentos. Con 429 el nombre y el comportamiento coinciden, y además
    coincide con el 429 que ya emite el throttling por IP: el frontend trata los
    dos casos de la misma forma, que es justo lo que quiere.

    Además de `error`, devuelve `retry_after_seconds` para que el formulario de
    login pueda mostrar un contador regresivo real en lugar de un texto fijo
    ("vuelve en 10 minutos") que el usuario no puede verificar.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Demasiados intentos fallidos. Espere antes de volver a intentar.'
    default_code = 'demasiados_intentos'

    def __init__(self, mensaje=None, retry_after_seconds=None):
        self.retry_after_seconds = max(0, int(retry_after_seconds or 0))

        # DRF lee `wait` y lo publica como cabecera HTTP Retry-After. Es lo que
        # permite que un cliente bien escrito sepa cuándo reintentar sin tener que
        # interpretar el cuerpo de la respuesta.
        if self.retry_after_seconds > 0:
            self.wait = self.retry_after_seconds

        super().__init__(detail=mensaje or self.default_detail)

        # `APIException.__init__` pasa el detalle por `_get_error_details()`, que
        # convierte CUALQUIER valor con `force_str()`. Si se le entregara el dict
        # completo, `retry_after_seconds` saldría en el JSON como la CADENA "600"
        # y no como el número 600. En el frontend eso obliga a coerciones
        # implícitas y rompe cualquier cuenta regresiva. Por eso el payload se arma
        # aquí, después de super(), con el entero intacto.
        self.detail = {
            'error': self.detail,
            'retry_after_seconds': self.retry_after_seconds,
        }


# --- Errores de CU2 (Recuperar contraseña) ---


class TokenRecuperacionInvalidoError(ErrorAutenticacion):
    """
    El enlace de recuperación no sirve: no existe, expiró, ya se usó, fue cancelado
    o agotó sus intentos.

    Es UNA sola excepción y por tanto un solo mensaje para los cinco casos. El
    servicio sí distingue internamente cada motivo (lo necesita la bitácora para
    detectar un intento de fuerza bruta), pero el motivo nunca viaja al cliente.

    Por qué no se separan en cinco mensajes: quien llama a este endpoint ya tiene
    el token en la mano, así que no necesita una explicación para actuar; y un
    mensaje distinto por caso convierte el endpoint en un oráculo. Con "este
    enlace ya no sirve, pedí uno nuevo" el usuario entiende exactamente lo mismo
    sin que se le abra ninguna puerta.
    """

    default_detail = (
        'Este enlace de recuperación ya no es válido. '
        'Solicitá uno nuevo desde la pantalla de acceso.'
    )
    default_code = 'token_recuperacion_invalido'


class ContrasenaDebilError(ErrorAutenticacion):
    """
    La contraseña nueva no cumple la política de seguridad del proyecto.

    Se sube como una sola cadena legible en lugar de un ValidationError de DRF
    porque el frontend ya tiene el contrato `{"error": "<mensaje>"}` y con una
    lista de mensajes tendría que recorrer un array para pintar un texto.

    El detalle va envuelto en `{'error': ...}` a propósito: un `detail` de tipo
    texto plano lo convertiría DRF en `{"detail": ...}`, que es OTRO contrato y
    rompería el `setError()` del frontend igual que un ValidationError.
    """

    default_code = 'contrasena_debil'

    def __init__(self, errores):
        self.errores = list(errores)
        mensaje = ' '.join(self.errores) or 'La contraseña no cumple la política de seguridad.'
        super().__init__(detail={'error': mensaje})
