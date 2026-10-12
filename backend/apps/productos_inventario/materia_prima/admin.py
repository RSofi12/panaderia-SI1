from django.contrib import admin

from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
)


@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('id_materia_prima', 'nombre', 'unidad_medida', 'stock_minimo', 'activo', 'fecha_registro')
    list_filter = ('activo', 'unidad_medida')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_registro',)


@admin.register(InventarioMateriaPrima)
class InventarioMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('id_inventario', 'id_materia_prima', 'stock_actual')
    search_fields = ('id_materia_prima__nombre',)


@admin.register(HistorialPrecioMateriaPrima)
class HistorialPrecioMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('id_historial', 'id_materia_prima', 'precio', 'fecha_inicio')
    list_filter = ('id_materia_prima',)
    readonly_fields = ('fecha_inicio',)


@admin.register(MovimientoMateriaPrima)
class MovimientoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('id_movimiento', 'id_inventario', 'tipo', 'cantidad', 'fecha_hora', 'id_compra')
    list_filter = ('tipo', 'fecha_hora')
    readonly_fields = ('fecha_hora',)
