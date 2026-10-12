from django.contrib import admin

from apps.compras.compra_materia_prima.models import Compra, DetalleCompra


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id_compra', 'fecha_hora', 'id_proveedor', 'total', 'id_usuario')
    list_filter = ('fecha_hora', 'id_proveedor')
    search_fields = ('id_proveedor__nombre', 'id_usuario__username')
    readonly_fields = ('fecha_hora', 'total')
    inlines = [DetalleCompraInline]
