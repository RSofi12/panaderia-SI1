from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)
from .services.registrar_movimiento import registrar_movimiento


# =============================================================================
# CU20 — Entrada (POST /api/gastos/)
# =============================================================================

class MovimientoEconomicoRegistroSerializer(serializers.Serializer):
    """
    Cuerpo para registrar un gasto o una inversión.

    No es ModelSerializer: el create real lo hace registrar_movimiento(), que
    además deja la traza en bitácora. `id_usuario` no se acepta desde el
    cliente: el responsable sale de la sesión.
    """
    tipo = serializers.ChoiceField(choices=TipoMovimientoEconomico.choices)
    categoria = serializers.ChoiceField(
        choices=CategoriaMovimientoEconomico.choices,
        required=False,
        default=CategoriaMovimientoEconomico.OTROS,
    )
    concepto = serializers.CharField(max_length=100)
    monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fecha_hora = serializers.DateTimeField(required=False, allow_null=True)

    def validate_concepto(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El concepto no puede estar vacío.')
        return value

    def validate_fecha_hora(self, value):
        if value is not None and value > timezone.now():
            raise serializers.ValidationError('La fecha no puede ser futura.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        try:
            return registrar_movimiento(
                usuario=request.user,
                tipo=validated_data['tipo'],
                categoria=validated_data['categoria'],
                concepto=validated_data['concepto'],
                monto=validated_data['monto'],
                descripcion=validated_data.get('descripcion'),
                fecha_hora=validated_data.get('fecha_hora'),
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError(list(exc.messages)) from exc


# =============================================================================
# CU20 — Salida (respuesta API)
# =============================================================================

class MovimientoEconomicoSerializer(serializers.ModelSerializer):
    """Movimiento económico en lectura (listado y detalle)."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)

    class Meta:
        model = MovimientoEconomico
        fields = [
            'id_movimiento',
            'tipo',
            'tipo_display',
            'categoria',
            'categoria_display',
            'concepto',
            'descripcion',
            'monto',
            'fecha_hora',
            'anulado',
            'id_usuario',
            'registrado_por',
        ]
        read_only_fields = fields
