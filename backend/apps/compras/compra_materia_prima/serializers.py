from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Compra, DetalleCompra
from .services.registrar_compra import registrar_compra


# =============================================================================
# CU7 — Entrada (POST /api/compras/)
# =============================================================================

class CompraDetalleEntradaSerializer(serializers.Serializer):
    """Una línea del cuerpo del POST."""
    id_materia_prima = serializers.IntegerField(min_value=1)
    cantidad = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal('0.001'),
    )
    precio_unitario = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )


class CompraRegistroSerializer(serializers.Serializer):
    """
    Cuerpo para registrar una compra.
    No es ModelSerializer: el create real lo hace registrar_compra().
    """
    id_proveedor = serializers.IntegerField(min_value=1)
    detalles = CompraDetalleEntradaSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        request = self.context['request']
        lineas = [
            {
                'id_materia_prima': d['id_materia_prima'],
                'cantidad': d['cantidad'],
                'precio_unitario': d['precio_unitario'],
            }
            for d in validated_data['detalles']
        ]
        try:
            return registrar_compra(
                usuario=request.user,
                id_proveedor=validated_data['id_proveedor'],
                lineas=lineas,
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError(list(exc.messages)) from exc


# =============================================================================
# CU7 — Salida (respuesta API)
# =============================================================================

class CompraDetalleLecturaSerializer(serializers.ModelSerializer):
    """Línea de compra en lectura (con datos del catálogo)."""
    nombre_materia_prima = serializers.CharField(
        source='id_materia_prima.nombre',
        read_only=True,
    )
    unidad_medida = serializers.CharField(
        source='id_materia_prima.unidad_medida',
        read_only=True,
    )

    class Meta:
        model = DetalleCompra
        fields = [
            'id_detalle_compra',
            'id_materia_prima',
            'nombre_materia_prima',
            'unidad_medida',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]


class CompraSerializer(serializers.ModelSerializer):
    """Cabecera + detalles para detalle (GET id) y respuesta del POST."""
    proveedor_nombre = serializers.CharField(source='id_proveedor.nombre', read_only=True)
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    detalles = CompraDetalleLecturaSerializer(many=True, read_only=True)
    advertencias = serializers.SerializerMethodField()

    class Meta:
        model = Compra
        fields = [
            'id_compra',
            'id_proveedor',
            'proveedor_nombre',
            'registrado_por',
            'fecha_hora',
            'total',
            'detalles',
            'advertencias',
        ]
        read_only_fields = fields

    def get_advertencias(self, obj):
        return getattr(obj, 'advertencias', [])


class CompraListSerializer(serializers.ModelSerializer):
    """Listado GET /api/compras/ (sin nested detalles, optimizado con anotación)."""
    proveedor_nombre = serializers.CharField(source='id_proveedor.nombre', read_only=True)
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    cantidad_lineas = serializers.SerializerMethodField()

    class Meta:
        model = Compra
        fields = [
            'id_compra',
            'id_proveedor',
            'proveedor_nombre',
            'registrado_por',
            'fecha_hora',
            'total',
            'cantidad_lineas',
        ]

    def get_cantidad_lineas(self, obj):
        annotated = getattr(obj, 'cantidad_lineas', None)
        if annotated is not None:
            return annotated
        return obj.detalles.count()
