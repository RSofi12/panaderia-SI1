"""
Vistas de API para la gestión de Roles y Matriz de Permisos (CU4).
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.models import Rol
from apps.usuarios_seguridad.roles.serializers import (
    AsignarQuitarPermisoSerializer,
    MatrizPermisosSerializer,
    RolActualizarSerializer,
    RolCrearSerializer,
    RolDetalleSerializer,
    RolListSerializer,
)
from apps.usuarios_seguridad.roles.services import (
    asignar_permiso_a_rol,
    crear_rol,
    editar_rol,
    quitar_permiso_de_rol,
    reemplazar_permisos_rol,
)
from apps.usuarios_seguridad.users.permissions import TienePermiso


class RolViewSet(viewsets.ModelViewSet):
    """
    Controlador para el caso de uso CU04: Asignar roles y permisos.

    Endpoints expuestos:
    - GET   /api/roles/                       Lista de roles
    - POST  /api/roles/                       Alta de rol
    - GET   /api/roles/<id>/                  Detalle de un rol y sus permisos
    - PATCH /api/roles/<id>/                  Modificación de rol
    - PUT   /api/roles/<id>/permisos/         Reemplazo masivo de la matriz de permisos
    - POST  /api/roles/<id>/permisos/asignar/ Asignar permiso individual
    - POST  /api/roles/<id>/permisos/quitar/  Quitar permiso individual

    La eliminación física de roles (DELETE) está deliberadamente excluida:
    responde HTTP 405 Method Not Allowed.
    """
    queryset = Rol.objects.prefetch_related('permisos', 'usuarios').order_by('id_rol')
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    PERMISO_REQUERIDO = 'asignar_permisos'

    def get_permissions(self):
        return [TienePermiso(self.PERMISO_REQUERIDO)]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RolDetalleSerializer
        if self.action == 'create':
            return RolCrearSerializer
        if self.action in ['update', 'partial_update']:
            return RolActualizarSerializer
        return RolListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rol = crear_rol(
            nombre=serializer.validated_data['nombre'],
            descripcion=serializer.validated_data.get('descripcion'),
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )
        return Response(
            RolDetalleSerializer(rol, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        rol = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        rol_actualizado = editar_rol(
            rol=rol,
            datos=serializer.validated_data,
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )
        return Response(
            RolDetalleSerializer(rol_actualizado, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['put'], url_path='permisos')
    def permisos(self, request, pk=None):
        """
        Reemplaza la matriz completa de permisos asociados al rol.
        """
        rol = self.get_object()
        serializer = MatrizPermisosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rol_actualizado = reemplazar_permisos_rol(
            rol=rol,
            permisos_ids=serializer.validated_data['permisos'],
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )
        return Response(
            RolDetalleSerializer(rol_actualizado, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='permisos/asignar')
    def asignar(self, request, pk=None):
        """
        Asocia un permiso individual a este rol (+asignarPermiso() del diagrama de clases).
        """
        rol = self.get_object()
        serializer = AsignarQuitarPermisoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permiso = get_object_or_404(Permiso, pk=serializer.validated_data['id_permiso'])
        asignar_permiso_a_rol(
            rol=rol,
            permiso=permiso,
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )
        return Response(
            RolDetalleSerializer(rol, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='permisos/quitar')
    def quitar(self, request, pk=None):
        """
        Remueve un permiso individual de este rol (+quitarPermiso() del diagrama de clases).
        """
        rol = self.get_object()
        serializer = AsignarQuitarPermisoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permiso = get_object_or_404(Permiso, pk=serializer.validated_data['id_permiso'])
        quitar_permiso_de_rol(
            rol=rol,
            permiso=permiso,
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )
        return Response(
            RolDetalleSerializer(rol, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _ip(request):
        reenviado = request.META.get('HTTP_X_FORWARDED_FOR')
        if reenviado:
            return reenviado.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _agente(request):
        return (request.META.get('HTTP_USER_AGENT') or '')[:255] or None
