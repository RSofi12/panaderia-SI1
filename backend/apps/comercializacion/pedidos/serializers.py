from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.comercializacion.pedidos.models import DetallePedido, EstadoPedido, Pedido
from apps.comercializacion.ventas.serializers import DatosTarjetaEntradaSerializer
from apps.comercializacion.pedidos.services.cambiar_estado_pedido import cambiar_estado_pedido
from apps.comercializacion.pedidos.services.registrar_pedido import registrar_pedido
from apps.comercializacion.ventas.models import MetodoPago


class ClienteEntradaSerializer(serializers.Serializer):
    id_cliente = serializers.IntegerField(min_value=1, required=False)
    nombre = serializers.CharField(max_length=150, required=False, allow_blank=False)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get('id_cliente') and not (attrs.get('nombre') or '').strip():
            raise serializers.ValidationError(
                'Indica un cliente existente o el nombre de uno nuevo.'
            )
        return attrs


class PedidoDetalleEntradaSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class PedidoRegistroSerializer(serializers.Serializer):
    """El precio y el total los calcula registrar_pedido()."""
    cliente = ClienteEntradaSerializer()
    fecha_entrega = serializers.DateTimeField()
    metodo_pago = serializers.ChoiceField(choices=MetodoPago.choices)
    detalles = PedidoDetalleEntradaSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        request = self.context['request']
        try:
            return registrar_pedido(
                usuario=request.user,
                cliente=validated_data['cliente'],
                fecha_entrega=validated_data['fecha_entrega'],
                metodo_pago=validated_data['metodo_pago'],
                detalles=validated_data['detalles'],
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError(list(exc.messages)) from exc


class CambiarEstadoPedidoSerializer(serializers.Serializer):
    """Valida que el estado exista. El servicio decide si el salto es legal."""
    estado = serializers.ChoiceField(choices=EstadoPedido.choices)
    id_transaccion_stripe = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    datos_tarjeta = DatosTarjetaEntradaSerializer(required=False, allow_null=True)

    def update(self, instance, validated_data):
        request = self.context['request']
        try:
            return cambiar_estado_pedido(
                usuario=request.user,
                pedido_id=instance.pk,
                estado_nuevo=validated_data['estado'],
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
                datos_tarjeta=validated_data.get('datos_tarjeta'),
                id_transaccion_stripe=validated_data.get('id_transaccion_stripe'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError(list(exc.messages)) from exc


class DetallePedidoLecturaSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='id_producto.nombre', read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            'id_detalle_pedido',
            'id_producto',
            'nombre_producto',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]


class PedidoSerializer(serializers.ModelSerializer):
    cliente = serializers.CharField(source='id_cliente.nombre', read_only=True)
    id_cliente = serializers.IntegerField(source='id_cliente.id_cliente', read_only=True)
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    detalles = DetallePedidoLecturaSerializer(many=True, read_only=True)
    numero_comprobante = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id_pedido',
            'id_cliente',
            'cliente',
            'registrado_por',
            'fecha_registro',
            'fecha_entrega',
            'estado',
            'metodo_pago',
            'total',
            'numero_comprobante',
            'detalles',
        ]

    def get_numero_comprobante(self, obj):
        try:
            return obj.venta.numero_comprobante
        except ObjectDoesNotExist:
            return None
