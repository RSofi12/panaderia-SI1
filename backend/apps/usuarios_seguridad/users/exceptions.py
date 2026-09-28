"""
Errores de negocio de la sub-app `users` (CU3).

Se viven en su propio módulo, y no en `auth_app/exceptions.py`, por la misma
razón que los serializadores de CU3 no viven en `auth_app/serializers.py`: cada
sub-app es dueña de su superficie de error. `auth_app` responde a lo que pasa
por `/api/auth/`, y estas respuestas son de `/api/usuarios/`.

La forma del cuerpo importa y no es capricho. Estas excepciones heredan de
`APIException` y envuelven el mensaje en `{"error": "..."}` a propósito: si el
detalle fuera texto plano, DRF lo convertiría solo en `{"detail": "..."}`, que es
OTRO contrato, y el frontend que ya sabe leer `{error, detail}` en `LoginPage`
tendría que aprender un tercer formato. Si en cambio se usara
`serializers.ValidationError`, el mensaje saldría como `{"error": ["..."]}` con
el texto envuelto en una lista, y el `setError(...)` de React recibiría un array
donde espera una cadena.
"""
from rest_framework.exceptions import APIException


class OperacionInvalidaError(APIException):
    """
    Regla de negocio incumplida que no corresponde a un campo concreto.

    Se usa para las guardas que atraviesan varios campos a la vez: desactivar la
    propia cuenta, quitarse el propio rol, quedarse sin ningún Administrador.
    No son errores de validación de un input, así que no encajan en el formato
    `{"campo": ["mensaje"]}` que DRF usa para los formularios.

    Status 400 y no 403: la petición está bien formada y el servidor la entiende
    perfectamente; simplemente la combinación de valores que se pidió no es una
    operación que el sistema permita. Un 403 diría "no tenés permiso", que es
    otra cosa: el permiso se comprobó antes y sí se tiene.
    """

    status_code = 400
    default_code = 'operacion_invalida'

    def __init__(self, mensaje=None, codigo=None):
        self.mensaje = mensaje or 'La operación solicitada no está permitida.'
        super().__init__(detail={'error': self.mensaje}, code=codigo or self.default_code)
