from django.contrib import admin

from apps.comercializacion.ventas.models import DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('id_producto', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        'numero_comprobante',
        'fecha_hora',
        'metodo_pago',
        'id_transaccion_stripe',
        'total',
        'id_usuario',
    )
    list_filter = ('metodo_pago',)
    inlines = [DetalleVentaInline]
