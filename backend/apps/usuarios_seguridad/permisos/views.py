"""
Vistas de API para el catálogo de Permisos (CU4).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios_seguridad.users.permissions import TienePermiso
from .models import Permiso, ModuloPermiso
from .serializers import PermisoSerializer


class PermisoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catálogo de permisos del sistema (CU4).
    Solo lectura: no permite altas, modificaciones ni bajas directas por API.
    Protegido por el permiso 'asignar_permisos'.
    """
    queryset = Permiso.objects.all().order_by('modulo', 'id_permiso')
    serializer_class = PermisoSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    PERMISO_REQUERIDO = 'asignar_permisos'

    def get_permissions(self):
        return [TienePermiso(self.PERMISO_REQUERIDO)]

    def get_queryset(self):
        qs = super().get_queryset()
        modulo = self.request.query_params.get('modulo')
        if modulo:
            qs = qs.filter(modulo=modulo)
        return qs

    @action(detail=False, methods=['get'], url_path='agrupados')
    def agrupados(self, request):
        """
        Retorna el catálogo organizado por los 5 módulos/paquetes oficiales,
        facilitando el renderizado directo de la matriz de checkboxes en el frontend.
        """
        permisos = self.get_queryset()
        grupos = {}
        for modulo_val, modulo_lbl in ModuloPermiso.choices:
            grupos[modulo_val] = {
                'modulo': modulo_val,
                'modulo_display': modulo_lbl,
                'permisos': [],
            }

        for p in permisos:
            if p.modulo in grupos:
                grupos[p.modulo]['permisos'].append(PermisoSerializer(p).data)

        return Response(list(grupos.values()), status=status.HTTP_200_OK)
