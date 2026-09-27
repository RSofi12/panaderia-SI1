import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


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
