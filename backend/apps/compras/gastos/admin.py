from django.contrib import admin

from .models import MovimientoEconomico


@admin.register(MovimientoEconomico)
class MovimientoEconomicoAdmin(admin.ModelAdmin):
    list_display = ('id_movimiento', 'tipo', 'concepto', 'monto', 'fecha_hora', 'id_usuario')
    list_filter = ('tipo', 'fecha_hora')
    search_fields = ('concepto', 'descripcion')
