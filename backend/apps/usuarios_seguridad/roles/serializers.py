"""
Serializadores del módulo de Roles y Matriz de Permisos (CU4).
"""
from rest_framework import serializers

from apps.usuarios_seguridad.permisos.serializers import PermisoSerializer
from apps.usuarios_seguridad.roles.constants import ROLES_PROTEGIDOS
from apps.usuarios_seguridad.roles.models import Rol


class RolListSerializer(serializers.ModelSerializer):
    """
    Serializador para el listado de roles.
    Proporciona métricas rápidas (total de permisos y usuarios asignados)
    e indica si el rol es protegido por el sistema.
    """
    total_permisos = serializers.SerializerMethodField()
    total_usuarios = serializers.SerializerMethodField()
    es_protegido = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = [
            'id_rol',
            'nombre',
            'descripcion',
            'total_permisos',
            'total_usuarios',
            'es_protegido',
        ]

    def get_total_permisos(self, obj):
        return obj.permisos.count()

    def get_total_usuarios(self, obj):
        return getattr(obj, 'usuarios', None).count() if hasattr(obj, 'usuarios') else 0

    def get_es_protegido(self, obj):
        return obj.nombre in ROLES_PROTEGIDOS


class RolDetalleSerializer(serializers.ModelSerializer):
    """
    Serializador detallado de un rol individual con todos sus permisos asignados.
    """
    permisos = PermisoSerializer(many=True, read_only=True)
    total_permisos = serializers.SerializerMethodField()
    total_usuarios = serializers.SerializerMethodField()
    es_protegido = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = [
            'id_rol',
            'nombre',
            'descripcion',
            'es_protegido',
            'total_permisos',
            'total_usuarios',
            'permisos',
        ]

    def get_total_permisos(self, obj):
        return obj.permisos.count()

    def get_total_usuarios(self, obj):
        return getattr(obj, 'usuarios', None).count() if hasattr(obj, 'usuarios') else 0

    def get_es_protegido(self, obj):
        return obj.nombre in ROLES_PROTEGIDOS


class RolCrearSerializer(serializers.Serializer):
    """
    Validación de entrada para el alta de un nuevo rol.
    """
    nombre = serializers.CharField(max_length=50, required=True)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class RolActualizarSerializer(serializers.Serializer):
    """
    Validación de entrada para la modificación de un rol existente.
    """
    nombre = serializers.CharField(max_length=50, required=False)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MatrizPermisosSerializer(serializers.Serializer):
    """
    Payload para el reemplazo completo de la lista de permisos asignados a un rol.
    """
    permisos = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='Lista completa de IDs de permisos que pertenecerán a este rol.'
    )


class AsignarQuitarPermisoSerializer(serializers.Serializer):
    """
    Payload para las acciones puntuales asignarPermiso y quitarPermiso.
    """
    id_permiso = serializers.IntegerField(
        required=True,
        help_text='ID del permiso a asociar o desasociar.'
    )
