"""
Serializers para Producción Diaria (CU10) e Historial de Producción (CU11).
"""
from decimal import Decimal

from rest_framework import serializers

from apps.productos_inventario.productos.models import Producto
from .models import DetalleProduccion, JornadaProduccion, Produccion


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
    consumos_materia_prima = serializers.SerializerMethodField()

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
            'consumos_materia_prima',
        ]

    def get_total_unidades(self, obj):
        return sum(detalle.cantidad_producida for detalle in obj.detalles.all())

    def get_total_variedades(self, obj):
        return len(obj.detalles.all())

    def get_costo_total(self, obj):
        total = sum(
            Decimal(detalle.cantidad_producida) * detalle.costo_unitario
            for detalle in obj.detalles.all()
        )
        return str(total.quantize(Decimal('0.01')))

    def get_consumos_materia_prima(self, obj):
        movimientos = getattr(obj, 'movimientos_insumo', None)
        if movimientos is None:
            return []
        return [
            {
                'id_materia_prima': m.id_inventario.id_materia_prima_id,
                'nombre_insumo': m.id_inventario.id_materia_prima.nombre,
                'cantidad_descontada': float(m.cantidad),
                'unidad_medida': m.id_inventario.id_materia_prima.unidad_medida,
            }
            for m in movimientos.select_related('id_inventario__id_materia_prima').all()
        ]


class DetalleProduccionInputSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
    cantidad_producida = serializers.IntegerField(min_value=0)


class RegistrarProduccionInputSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    jornada = serializers.CharField(max_length=30, default=JornadaProduccion.MANANA)
    detalles = DetalleProduccionInputSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError('Debe proporcionar al menos un producto a elaborar.')
        if all(item.get('cantidad_producida', 0) <= 0 for item in value):
            raise serializers.ValidationError('Al menos un producto debe tener cantidad producida mayor a 0.')
        return value


class SimularConsumoInputSerializer(serializers.Serializer):
    detalles = DetalleProduccionInputSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError('Debe proporcionar al menos un producto para simular.')
        return value


class RecetaInsumoItemSerializer(serializers.Serializer):
    id_materia_prima = serializers.IntegerField(source='id_materia_prima.id_materia_prima')
    nombre_insumo = serializers.CharField(source='id_materia_prima.nombre')
    unidad_medida = serializers.CharField(source='id_materia_prima.unidad_medida')
    cantidad_requerida = serializers.FloatField()


class RecetaProductoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='nombre')
    insumos = RecetaInsumoItemSerializer(source='receta_detalles', many=True)

    class Meta:
        model = Producto
        fields = [
            'id_producto',
            'nombre_producto',
            'insumos',
        ]
