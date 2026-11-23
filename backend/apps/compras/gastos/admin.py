from django.contrib import admin

from .models import MovimientoEconomico


@admin.register(MovimientoEconomico)
class MovimientoEconomicoAdmin(admin.ModelAdmin):
    list_display = (
        'id_movimiento', 'tipo', 'categoria', 'concepto', 'monto',
        'fecha_hora', 'anulado', 'id_usuario',
    )
    list_filter = ('tipo', 'categoria', 'anulado', 'fecha_hora')
    search_fields = ('concepto', 'descripcion')
