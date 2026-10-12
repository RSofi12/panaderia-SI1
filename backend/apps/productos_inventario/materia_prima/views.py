from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.materia_prima.serializers import (
    MateriaPrimaSerializer,
    MateriaPrimaStockSerializer,
)


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


class MateriaPrimaStockListView(APIView):
    """GET /api/inventario/materias-primas/ — Consulta de stock (CU8)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        materias = MateriaPrima.objects.select_related('inventario')

        nombre = request.query_params.get('nombre')
        activo = request.query_params.get('activo')
        bajo_minimo = request.query_params.get('bajo_minimo')

        if nombre:
            materias = materias.filter(nombre__icontains=nombre.strip())
        if activo in ('true', 'false'):
            materias = materias.filter(activo=(activo == 'true'))
        else:
            materias = materias.filter(activo=True)
        if bajo_minimo == 'true':
            materias = materias.filter(inventario__stock_actual__lte=F('stock_minimo'))

        return Response(MateriaPrimaStockSerializer(materias, many=True).data)
