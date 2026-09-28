from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ConfiguracionSeguridad(models.Model):
    """
    Parámetros editables de la política de seguridad (CU1 y CU2).

    Diseño: patrón Singleton con clave primaria fija en 1. La tabla tiene
    exactamente una fila; el administrador podrá editarla desde el panel de Django
    sin necesidad de un despliegue, y más adelante desde el dashboard del
    Administrador (CU3).

    Se modela en base de datos (y no en settings.py) por dos razones:
      1. La política es dato de negocio, no configuración de despliegue.
      2. El requisito de que el Administrador pueda gestionar los intentos
         máximos exige que el valor viva en la BD y sea auditable.

    Los tres campos de CU2 (`minutos_expiracion_token`, `max_intentos_token` y
    `max_solicitudes_por_hora`) viven aquí y no en el modelo TokenRecuperacion
    por la misma razón: son política global, y si estuvieran en el token cada
    fila arrastraría su propia copia de la regla y un cambio de política exigiría
    reescribir el histórico.
    """

    LIMITE_MAXIMO_INTENTOS = 20
    LIMITE_MAXIMO_MINUTOS = 1440  # 24 horas
    LIMITE_MAXIMO_SOLICITUDES_HORA = 20

    id_configuracion = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
        verbose_name='ID de configuración'
    )
    max_intentos_fallidos = models.PositiveSmallIntegerField(
        default=3,
        db_default=3,
        verbose_name='Máximo de intentos fallidos',
        help_text='Intentos consecutivos con contraseña incorrecta antes de bloquear la cuenta.'
    )
    minutos_bloqueo = models.PositiveIntegerField(
        default=10,
        db_default=10,
        verbose_name='Minutos de bloqueo',
        help_text='Duración del bloqueo tras alcanzar el máximo de intentos fallidos.'
    )

    # --- Política de recuperación de contraseña (CU2) ---

    minutos_expiracion_token = models.PositiveSmallIntegerField(
        default=15,
        db_default=15,
        verbose_name='Minutos de expiración del token',
        help_text='Ventana de validez del enlace de recuperación de contraseña (CU2).'
    )
    max_intentos_token = models.PositiveSmallIntegerField(
        default=5,
        db_default=5,
        verbose_name='Máximo de intentos por token',
        help_text='Confirmaciones fallidas con un mismo enlace antes de invalidarlo (CU2).'
    )
    max_solicitudes_por_hora = models.PositiveSmallIntegerField(
        default=3,
        db_default=3,
        verbose_name='Máximo de solicitudes por hora',
        help_text='Enlaces de recuperación que una misma cuenta puede pedir por hora (CU2).'
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuraciones_seguridad_actualizadas',
        verbose_name='Actualizado por'
    )

    class Meta:
        db_table = 'configuracion_seguridad'
        verbose_name = 'Configuración de Seguridad'
        verbose_name_plural = 'Configuraciones de Seguridad'
        constraints = [
            models.CheckConstraint(
                condition=Q(id_configuracion=1),
                name='configuracion_seguridad_singleton',
            ),
            models.CheckConstraint(
                condition=Q(max_intentos_fallidos__gte=1, max_intentos_fallidos__lte=20),
                name='configuracion_seguridad_rango_intentos',
            ),
            models.CheckConstraint(
                condition=Q(minutos_bloqueo__gte=1, minutos_bloqueo__lte=1440),
                name='configuracion_seguridad_rango_minutos',
            ),
            models.CheckConstraint(
                condition=Q(minutos_expiracion_token__gte=1, minutos_expiracion_token__lte=1440),
                name='configuracion_seguridad_rango_expiracion_token',
            ),
            models.CheckConstraint(
                condition=Q(max_intentos_token__gte=1, max_intentos_token__lte=20),
                name='configuracion_seguridad_rango_intentos_token',
            ),
            models.CheckConstraint(
                condition=Q(
                    max_solicitudes_por_hora__gte=1,
                    max_solicitudes_por_hora__lte=20,
                ),
                name='configuracion_seguridad_rango_solicitudes_hora',
            ),
        ]

    def __str__(self):
        return (
            f'Política: {self.max_intentos_fallidos} intentos '
            f'→ bloqueo de {self.minutos_bloqueo} minutos'
        )

    def save(self, *args, **kwargs):
        """Fuerza la clave primaria a 1 para preservar la invariante de singleton."""
        self.id_configuracion = 1
        return super().save(*args, **kwargs)

    def clean(self):
        if not 1 <= self.max_intentos_fallidos <= self.LIMITE_MAXIMO_INTENTOS:
            raise ValidationError({
                'max_intentos_fallidos':
                    f'Debe estar entre 1 y {self.LIMITE_MAXIMO_INTENTOS}.'
            })
        if not 1 <= self.minutos_bloqueo <= self.LIMITE_MAXIMO_MINUTOS:
            raise ValidationError({
                'minutos_bloqueo':
                    f'Debe estar entre 1 y {self.LIMITE_MAXIMO_MINUTOS} minutos.'
            })
        if not 1 <= self.minutos_expiracion_token <= self.LIMITE_MAXIMO_MINUTOS:
            raise ValidationError({
                'minutos_expiracion_token':
                    f'Debe estar entre 1 y {self.LIMITE_MAXIMO_MINUTOS} minutos.'
            })
        if not 1 <= self.max_intentos_token <= self.LIMITE_MAXIMO_INTENTOS:
            raise ValidationError({
                'max_intentos_token':
                    f'Debe estar entre 1 y {self.LIMITE_MAXIMO_INTENTOS}.'
            })
        if not 1 <= self.max_solicitudes_por_hora <= self.LIMITE_MAXIMO_SOLICITUDES_HORA:
            raise ValidationError({
                'max_solicitudes_por_hora':
                    f'Debe estar entre 1 y {self.LIMITE_MAXIMO_SOLICITUDES_HORA}.'
            })


    @classmethod
    def cargar(cls):
        """
        Devuelve la fila de configuración, creándola con los valores por defecto
        la primera vez. Se usa como punto de acceso único en todo el backend.
        """
        instancia, _ = cls.objects.get_or_create(id_configuracion=1)
        return instancia
