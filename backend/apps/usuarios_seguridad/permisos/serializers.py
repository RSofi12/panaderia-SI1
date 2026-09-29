"""
Serializadores del módulo de Permisos (CU4).
"""
from rest_framework import serializers
from .models import Permiso, ModuloPermiso


class PermisoSerializer(serializers.ModelSerializer):
    """
    Serializador completo del catálogo de permisos.
    Incluye el módulo para permitir agrupaciones en la interfaz.
    """
    modulo_display = serializers.CharField(source='get_modulo_display', read_only=True)

    class Meta:
        model = Permiso
        fields = [
            'id_permiso',
            'nombre',
            'descripcion',
            'modulo',
            'modulo_display',
        ]
        read_only_fields = ['id_permiso']
