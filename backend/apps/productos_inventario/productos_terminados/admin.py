from django.contrib import admin

from .models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
)


@admin.register(InventarioProductoTerminado)
class InventarioProductoTerminadoAdmin(admin.ModelAdmin):
    list_display = ('id_inventario', 'id_producto', 'stock_actual')
    search_fields = ('id_producto__nombre',)


@admin.register(MovimientoProductoTerminado)
class MovimientoProductoTerminadoAdmin(admin.ModelAdmin):
    list_display = ('id_movimiento', 'id_inventario', 'tipo', 'cantidad', 'fecha_hora')
    list_filter = ('tipo', 'fecha_hora')


@admin.register(NotaPerdidaProducto)
class NotaPerdidaProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id_nota_perdida',
        'id_detalle_produccion',
        'cantidad',
        'costo_unitario',
        'fecha_salida',
    )
    list_filter = ('fecha_salida',)
