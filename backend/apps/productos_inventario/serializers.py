from decimal import Decimal

from rest_framework import serializers

from .models import CategoriaProducto, Producto


class CategoriaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = ['id_categoria', 'nombre', 'descripcion']


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializador del catálogo de productos (CU5).
    El precio sugerido lo calcula el modelo a partir del costo y el porcentaje de ganancia.
    """
    categoria_nombre = serializers.CharField(source='id_categoria.nombre', read_only=True, default=None)

    class Meta:
        model = Producto
        fields = [
            'id_producto',
            'id_categoria',
            'categoria_nombre',
            'nombre',
            'descripcion',
            'costo_produccion',
            'porcentaje_ganancia',
            'precio_sugerido',
            'precio_venta',
            'fecha_registro',
            'activo',
        ]
        read_only_fields = ['id_producto', 'precio_sugerido', 'fecha_registro']

    def validate_nombre(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError('El nombre del producto es obligatorio.')
        return nombre

    def validate_costo_produccion(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError('El costo de producción no puede ser negativo.')
        return value

    def validate_porcentaje_ganancia(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError('El porcentaje de ganancia no puede ser negativo.')
        return value

    def validate_precio_venta(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('El precio de venta debe ser mayor a cero.')
        return value
