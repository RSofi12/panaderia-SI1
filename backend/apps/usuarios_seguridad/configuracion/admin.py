from django.contrib import admin
from .models import ConfiguracionSeguridad


@admin.register(ConfiguracionSeguridad)
class ConfiguracionSeguridadAdmin(admin.ModelAdmin):
    """
    El panel expone una única fila editable: los intentos máximos y los minutos
    de bloqueo dejan de estar codificados en el código fuente.
    """

    list_display = (
        'id_configuracion',
        'max_intentos_fallidos',
        'minutos_bloqueo',
        'minutos_expiracion_token',
        'max_intentos_token',
        'max_solicitudes_por_hora',
        'actualizado_en',
        'actualizado_por',
    )
    readonly_fields = ('actualizado_en', 'actualizado_por')

    def has_add_permission(self, request):
        return not ConfiguracionSeguridad.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
