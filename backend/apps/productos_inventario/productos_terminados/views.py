"""
Vistas para Existencias de Productos Terminados (CU12) y Bajas/Mermas (CU18).
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InventarioProductoTerminado, NotaPerdidaProducto
from .serializers import (
    InventarioProductoTerminadoSerializer,
    NotaPerdidaProductoSerializer,
)


class InventarioProductoTerminadoListView(APIView):
    """
    GET /api/productos-terminados/existencias/ — Existencias de pan terminado listo para la venta (CU12).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventarios = InventarioProductoTerminado.objects.select_related(
            'id_producto__id_categoria'
        ).order_by('id_producto__nombre')
        return Response(InventarioProductoTerminadoSerializer(inventarios, many=True).data)


class NotaPerdidaProductoListCreateView(APIView):
    """
    GET  /api/productos-terminados/mermas/ — Historial de bajas de producto terminado (CU18).
    POST /api/productos-terminados/mermas/ — Registrar baja/merma descontando stock (CU18 - Ciclo 3).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notas = NotaPerdidaProducto.objects.select_related(
            'id_detalle_produccion__id_producto',
            'id_usuario',
        ).order_by('-fecha_salida')
        return Response(NotaPerdidaProductoSerializer(notas, many=True).data)
