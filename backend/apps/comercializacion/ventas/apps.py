from django.apps import AppConfig


class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comercializacion.ventas'
    label = 'ventas'
    verbose_name = 'Ventas de mostrador'
