"""
Serializers para Producción Diaria e Historial (CU10, CU11).
"""
from rest_framework import serializers

from .models import DetalleProduccion, Produccion


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
