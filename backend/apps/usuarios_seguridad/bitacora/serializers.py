from rest_framework import serializers
from .models import Bitacora


class BitacoraSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)

    class Meta:
        model = Bitacora
        fields = (
            'id_bitacora',
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'nombre_usuario_intento',
            'accion',
            'tabla_afectada',
            'descripcion',
            'fecha_hora',
        )
        read_only_fields = fields
