from decimal import Decimal

from rest_framework import serializers

from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado

class DisponibilidadProductoSerializer(serializers.ModelSerializer):
    id_producto = serializers.IntegerField(source='id_producto.id_producto', read_only=True)
    nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    categoria = serializers.CharField(source='id_producto.id_categoria.nombre', default='Sin categoría', read_only=True)
    precio_venta = serializers.DecimalField(source='id_producto.precio_venta', max_digits=10, decimal_places=2, read_only=True)
    valor_disponible = serializers.SerializerMethodField()

    class Meta:
        model = InventarioProductoTerminado
        fields = ['id_producto', 'nombre', 'categoria', 'stock_actual', 'precio_venta', 'valor_disponible']

    def get_valor_disponible(self, obj):
        precio = obj.id_producto.precio_venta or Decimal('0.00')
        return str((obj.stock_actual * precio).quantize(Decimal('0.01')))
