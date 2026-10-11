import re
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.compras.services.registrar_compra import registrar_compra

from .models import Compra, DetalleCompra, Proveedor

# Teléfono boliviano típico: 7–8 dígitos locales, o +591 + 8 dígitos.
# Se aceptan espacios, guiones y paréntesis al escribir; se guardan solo dígitos
# (y un '+' inicial si vino el código de país).
TELEFONO_LIMPIO = re.compile(r'^\+?\d{7,15}$')


def normalizar_telefono(valor: str) -> str:
    compacto = re.sub(r'[\s().-]', '', valor.strip())
    return compacto


class ProveedorSerializer(serializers.ModelSerializer):
    """
    Serializador del maestro de proveedores (CU6).
    Nombre, teléfono y dirección son obligatorios en el caso de uso;
    el estado (activo) no se edita aquí: va por toggle-activo.
    """

    class Meta:
        model = Proveedor
        fields = [
            'id_proveedor',
            'nombre',
            'telefono',
            'direccion',
            'fecha_registro',
            'activo',
        ]
        read_only_fields = ['id_proveedor', 'fecha_registro', 'activo']
        # En el modelo (y en el DDL) teléfono y dirección admiten NULL, así que
        # DRF los trataría como opcionales y un alta sin ellos nunca llegaría a
        # validate_telefono/validate_direccion.
        extra_kwargs = {
            'telefono': {
                'required': True,
                'allow_null': False,
                'error_messages': {'required': 'El teléfono del proveedor es obligatorio.'},
            },
            'direccion': {
                'required': True,
                'allow_null': False,
                'error_messages': {'required': 'La dirección del proveedor es obligatoria.'},
            },
        }

    def validate_nombre(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError('El nombre del proveedor es obligatorio.')

        qs = Proveedor.objects.filter(nombre__iexact=nombre)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un proveedor con ese nombre.')
        return nombre

    def validate_telefono(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError('El teléfono del proveedor es obligatorio.')

        telefono = normalizar_telefono(str(value))
        if not TELEFONO_LIMPIO.match(telefono):
            raise serializers.ValidationError(
                'Ingresa un teléfono válido (7 a 15 dígitos; se admite +591).'
            )

        qs = Proveedor.objects.filter(telefono=telefono)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un proveedor con ese teléfono.')
        return telefono

    def validate_direccion(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError('La dirección del proveedor es obligatoria.')
        return str(value).strip()


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
        ]
        read_only_fields = fields


class CompraListSerializer(serializers.ModelSerializer):
    """Listado GET /api/compras/ (sin nested detalles)."""
    proveedor_nombre = serializers.CharField(source='id_proveedor.nombre', read_only=True)
    registrado_por = serializers.CharField(source='id_usuario.nombre_usuario', read_only=True)
    cantidad_lineas = serializers.IntegerField(source='detalles.count', read_only=True)

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

