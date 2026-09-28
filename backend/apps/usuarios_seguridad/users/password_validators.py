import re
# El import se aliasea porque la función pública del módulo se llama igual que la
# de Django. Antes de este alias, `validar_contrasena()` llamaba a SÍ MISMA con el
# keyword `usuario=`, que no existe: reventaba con TypeError en la primera
# invocación. La función estaba muerta desde que se escribió, esperando a que
# alguien la usara de verdad; el CU2 es el primer caso que la llama.
from django.contrib.auth.password_validation import (
    validate_password as validar_con_politica_de_django,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validar_contrasena(contrasena, usuario=None):
    """
    Ejecuta TODA la política de contraseñas de settings.AUTH_PASSWORD_VALIDATORS
    y devuelve la lista de errores como texto legible.

    Dónde se usa: al CREAR o MODIFICAR una contraseña (CU3 y el reset del CU2).
    Dónde NO se usa: en el login. Validar complejidad al iniciar sesión es un
    error de diseño: obligaría a que TODA contraseña histórica cumpliera la
    política vigente y dejaría sin salida a un usuario cuya contraseña fue
    creada con reglas más débiles. Al entrar solo se comprueba que la contraseña
    sea la correcta.

    `usuario` es opcional y sirve para el validador de similitud, que rechaza
    contraseñas parecidas al nombre de usuario.
    """
    try:
        validar_con_politica_de_django(contrasena, user=usuario)
    except ValidationError as error:
        return list(error.messages)
    return []


class ComplexPasswordValidator:
    """
    Validador personalizado de contraseñas para Panadería Santiago.
    Exige:
    - Longitud mínima de 8 caracteres.
    - Al menos una letra mayúscula (A-Z).
    - Al menos un dígito numérico (0-9).
    - Al menos un carácter especial (!, @, #, $, %, ^, &, *, ?, _, -, =, +, etc.).
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"La contraseña debe tener al menos {self.min_length} caracteres."),
                code='password_too_short',
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )

        if not re.search(r'\d', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_digit',
            )

        if not re.search(r'[!@#$%^&*(),.?":{}|<>=_+\-\\\/\[\]]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un carácter especial (ej. !@#$%^&*-_+=)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            f"Su contraseña debe contener al menos {self.min_length} caracteres, "
            "incluyendo al menos una letra mayúscula, un número y un carácter especial (!@#$%^&*-_+=)."
        )
