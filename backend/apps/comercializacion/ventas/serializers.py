from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.comercializacion.ventas.models import DetalleVenta, MetodoPago, Venta
from apps.comercializacion.ventas.services.registrar_venta import registrar_venta


class VentaDetalleEntradaSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class VentaRegistroSerializer(serializers.Serializer):
    """El precio y el total los calcula registrar_venta()."""
    metodo_pago = serializers.ChoiceField(choices=MetodoPago.choices)
    id_transaccion_stripe = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    detalles = VentaDetalleEntradaSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        metodo = attrs.get('metodo_pago')
        stripe_id = (attrs.get('id_transaccion_stripe') or '').strip()
        if metodo == MetodoPago.STRIPE and not stripe_id:
            raise serializers.ValidationError({
                'id_transaccion_stripe': 'La venta con Stripe requiere el id de la transacción.'
            })
        if metodo == MetodoPago.EFECTIVO and stripe_id:
            raise serializers.ValidationError({
                'id_transaccion_stripe': 'Una venta en efectivo no debe incluir id de transacción Stripe.'
            })
        attrs['id_transaccion_stripe'] = stripe_id or None
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        try:
            return registrar_venta(
                usuario=request.user,
                metodo_pago=validated_data['metodo_pago'],
                id_transaccion_stripe=validated_data.get('id_transaccion_stripe'),
                detalles=validated_data['detalles'],
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError(list(exc.messages)) from exc


class DetallesCotizacionSerializer(serializers.Serializer):
    """Cuerpo de la intención de cobro Stripe: solo productos y cantidades."""
    detalles = VentaDetalleEntradaSerializer(many=True, allow_empty=False)


class DetalleVentaLecturaSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='id_producto.nombre', read_only=True)

    class Meta:
        model = DetalleVenta
        fields = [
            'id_detalle_venta',
            'id_producto',
            'nombre_producto',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]


class VentaSerializer(serializers.ModelSerializer):
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    detalles = DetalleVentaLecturaSerializer(many=True, read_only=True)
    stock_resultante = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            'id_venta',
            'numero_comprobante',
            'fecha_hora',
            'metodo_pago',
            'id_transaccion_stripe',
            'total',
            'registrado_por',
            'detalles',
            'stock_resultante',
        ]
        read_only_fields = fields

    def get_stock_resultante(self, obj):
        return getattr(obj, 'stock_resultante', [])


class VentaListSerializer(serializers.ModelSerializer):
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    cantidad_lineas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id_venta',
            'numero_comprobante',
            'fecha_hora',
            'metodo_pago',
            'id_transaccion_stripe',
            'total',
            'registrado_por',
            'cantidad_lineas',
        ]
