"""
Serializers para Producción e Inventario Terminado (CU10, CU11, CU12, CU18).
"""
from rest_framework import serializers

from .models import (
    DetalleProduccion,
    InventarioProductoTerminado,
    NotaPerdidaProducto,
    Produccion,
)


class DetalleProduccionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)

    class Meta:
        model = DetalleProduccion
        fields = [
            'id_detalle_produccion',
            'id_producto',
            'producto_nombre',
            'cantidad_producida',
            'costo_unitario',
        ]


class ProduccionSerializer(serializers.ModelSerializer):
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    detalles = DetalleProduccionSerializer(many=True, read_only=True)

    class Meta:
        model = Produccion
        fields = [
            'id_produccion',
            'id_usuario',
            'registrado_por',
            'fecha',
            'jornada',
            'detalles',
        ]


class InventarioProductoTerminadoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='id_producto.id_categoria.nombre', read_only=True)

    class Meta:
        model = InventarioProductoTerminado
        fields = [
            'id_inventario',
            'id_producto',
            'producto_nombre',
            'categoria_nombre',
            'stock_actual',
        ]


class NotaPerdidaProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source='id_detalle_produccion.id_producto.nombre', read_only=True
    )
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)

    class Meta:
        model = NotaPerdidaProducto
        fields = [
            'id_nota_perdida',
            'id_detalle_produccion',
            'producto_nombre',
            'id_usuario',
            'registrado_por',
            'cantidad',
            'costo_unitario',
            'fecha_salida',
        ]
