from decimal import Decimal

from rest_framework import serializers

from apps.productos_inventario.productos.models import (
    CategoriaProducto,
    HistorialPrecioProducto,
    Producto,
)


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


class FiltrosHistorialPreciosSerializer(serializers.Serializer):
    """Parámetros opcionales del listado CU19; no cambia datos del catálogo."""

    id_producto = serializers.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807
    )
    fecha_desde = serializers.DateField(required=False, input_formats=['iso-8601'])
    fecha_hasta = serializers.DateField(required=False, input_formats=['iso-8601'])

    def validate(self, attrs):
        desde = attrs.get('fecha_desde')
        hasta = attrs.get('fecha_hasta')
        if desde and hasta and desde > hasta:
            raise serializers.ValidationError({
                'fecha_hasta': 'La fecha final no puede ser anterior a la fecha inicial.'
            })
        return attrs


class HistorialPrecioProductoSerializer(serializers.ModelSerializer):
    """Contrato de consulta: el precio se conserva como cadena decimal exacta."""

    id_producto = serializers.IntegerField(source='id_producto_id', read_only=True)
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    producto_activo = serializers.BooleanField(source='id_producto.activo', read_only=True)
    precio = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=True, read_only=True
    )

    class Meta:
        model = HistorialPrecioProducto
        fields = [
            'id_historial', 'id_producto', 'producto_nombre',
            'producto_activo', 'precio', 'fecha_inicio',
        ]
        read_only_fields = fields
