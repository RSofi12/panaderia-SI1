from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.materia_prima.permissions import EsRolAutorizadoCU09
from apps.productos_inventario.materia_prima.selectors import obtener_materias_primas_bajo_stock
from apps.productos_inventario.materia_prima.serializers import AlertaBajoStockSerializer
from apps.usuarios_seguridad.users.permissions import TienePermiso
from apps.productos_inventario.materia_prima.serializers import MateriaPrimaSerializer


class MateriaPrimaListView(APIView):
    """GET /api/materias-primas/ — Insumos con stock y último precio (CU7 / catálogo de compras)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        materias = MateriaPrima.objects.prefetch_related('inventario', 'historial_precios')

        nombre = request.query_params.get('nombre')
        activo = request.query_params.get('activo')

        if nombre:
            materias = materias.filter(nombre__icontains=nombre.strip())
        if activo in ('true', 'false'):
            materias = materias.filter(activo=(activo == 'true'))

        materias = materias.order_by('nombre')
        return Response(MateriaPrimaSerializer(materias, many=True).data)


class AlertasBajoStockView(APIView):
    """CU09: Consultar alertas de bajo stock de materias primas."""

    def get_permissions(self):
        return [
            TienePermiso('gestionar_inventario'),
            EsRolAutorizadoCU09(),
        ]

    def get(self, request):
        materias = obtener_materias_primas_bajo_stock()
        serializer = AlertaBajoStockSerializer(materias, many=True)
        return Response(serializer.data)
