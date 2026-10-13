"""
Serializers para Producción Diaria e Historial (CU10, CU11).
"""
from decimal import Decimal

from rest_framework import serializers

from .models import DetalleProduccion, Produccion


class DetalleProduccionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetalleProduccion
        fields = [
            'id_detalle_produccion',
            'id_producto',
            'producto_nombre',
            'cantidad_producida',
            'costo_unitario',
            'subtotal',
        ]

    def get_subtotal(self, obj):
        return str((Decimal(obj.cantidad_producida) * obj.costo_unitario).quantize(Decimal('0.01')))


class ProduccionSerializer(serializers.ModelSerializer):
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    detalles = DetalleProduccionSerializer(many=True, read_only=True)
    total_unidades = serializers.SerializerMethodField()
    total_variedades = serializers.SerializerMethodField()
    costo_total = serializers.SerializerMethodField()

    class Meta:
        model = Produccion
        fields = [
            'id_produccion',
            'id_usuario',
            'registrado_por',
            'fecha',
            'jornada',
            'total_unidades',
            'total_variedades',
            'costo_total',
            'detalles',
        ]

    def get_total_unidades(self, obj):
        return sum(detalle.cantidad_producida for detalle in obj.detalles.all())

    def get_total_variedades(self, obj):
        return obj.detalles.count()

    def get_costo_total(self, obj):
        total = sum(
            Decimal(detalle.cantidad_producida) * detalle.costo_unitario
            for detalle in obj.detalles.all()
        )
        return str(total.quantize(Decimal('0.01')))
