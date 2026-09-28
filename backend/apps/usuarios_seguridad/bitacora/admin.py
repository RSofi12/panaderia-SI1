from django.contrib import admin
from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = (
        'id_bitacora',
        'fecha_hora',
        'usuario',
        'nombre_usuario_intento',
        'accion',
        'tabla_afectada',
    )
    list_filter = ('accion', 'tabla_afectada', 'fecha_hora')
    search_fields = (
        'usuario__nombre_usuario',
        'usuario__nombre_completo',
        'nombre_usuario_intento',
        'accion',
        'descripcion',
    )
    # La bitácora es de solo lectura por definición: si se pudiera editar desde
    # el panel, dejaría de ser una evidencia auditable.
    readonly_fields = ('id_bitacora', 'usuario', 'nombre_usuario_intento', 'accion',
                       'tabla_afectada', 'descripcion', 'fecha_hora')
    ordering = ('-fecha_hora',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
