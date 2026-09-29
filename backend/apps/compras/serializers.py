import re

from rest_framework import serializers

from .models import Proveedor

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
