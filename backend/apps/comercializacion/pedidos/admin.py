from django.contrib import admin

from apps.comercializacion.pedidos.models import Cliente, DetallePedido, Pedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('id_producto', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion')
    search_fields = ('nombre', 'telefono')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id_pedido',
        'id_cliente',
        'fecha_registro',
        'fecha_entrega',
        'estado',
        'metodo_pago',
        'total',
        'id_usuario',
    )
    list_filter = ('estado', 'metodo_pago')
    inlines = [DetallePedidoInline]
