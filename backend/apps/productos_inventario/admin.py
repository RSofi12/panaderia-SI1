from django.contrib import admin

from .models import CategoriaProducto, HistorialPrecioProducto, Producto


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('id_categoria', 'nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id_producto', 'nombre', 'id_categoria', 'costo_produccion',
        'porcentaje_ganancia', 'precio_sugerido', 'precio_venta', 'activo',
    )
    list_filter = ('activo', 'id_categoria')
    search_fields = ('nombre',)
    readonly_fields = ('precio_sugerido', 'fecha_registro')


@admin.register(HistorialPrecioProducto)
class HistorialPrecioProductoAdmin(admin.ModelAdmin):
    list_display = ('id_historial', 'id_producto', 'precio', 'fecha_inicio')
    list_filter = ('id_producto',)
    readonly_fields = ('fecha_inicio',)
