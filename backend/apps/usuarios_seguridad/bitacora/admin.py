from django.contrib import admin
from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('id_bitacora', 'fecha_hora', 'usuario', 'accion', 'tabla_afectada')
    list_filter = ('accion', 'tabla_afectada', 'fecha_hora')
    search_fields = ('usuario__nombre_usuario', 'usuario__nombre_completo', 'accion', 'descripcion')
    readonly_fields = ('fecha_hora',)
    ordering = ('-fecha_hora',)
