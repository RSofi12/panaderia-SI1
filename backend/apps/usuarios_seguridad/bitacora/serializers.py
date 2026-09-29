from rest_framework import serializers
from .models import Bitacora


class BitacoraSerializer(serializers.ModelSerializer):
    """
    Un registro de auditoría tal como lo consulta CU26. Todo es de solo lectura:
    la bitácora la escribe el backend (`Bitacora.registrar`), nunca la API.
    """
    # La FK del modelo se llama `usuario` (columna `id_usuario`); el nombre
    # `id_usuario` no existe como atributo y hay que leerlo de `usuario_id`.
    id_usuario = serializers.IntegerField(source='usuario_id', read_only=True)
    # Un intento fallido no tiene usuario; sin `default` DRF omitiría la clave
    # en esas filas en lugar de devolver null.
    nombre_usuario = serializers.CharField(source='usuario.nombre_usuario', read_only=True, default=None)
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True, default=None)
    accion_etiqueta = serializers.CharField(source='get_accion_display', read_only=True)

    class Meta:
        model = Bitacora
        fields = (
            'id_bitacora',
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'nombre_usuario_intento',
            'accion',
            'accion_etiqueta',
            'tabla_afectada',
            'descripcion',
            'agente_usuario',
            'fecha_hora',
        )
        read_only_fields = fields
