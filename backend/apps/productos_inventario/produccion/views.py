"""
Vistas para Producción e Inventario Terminado.
Endpoints:
  - CU10/CU11: Producción y su historial
  - CU12: Existencias de productos terminados
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InventarioProductoTerminado, Produccion
from .serializers import (
    InventarioProductoTerminadoSerializer,
    ProduccionSerializer,
)


class ProduccionListCreateView(APIView):
    """
    GET  /api/produccion/ — Historial de producciones (CU11)
    POST /api/produccion/ — Registrar producción diaria (CU10 - a implementar en Ciclo 2)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        producciones = Produccion.objects.select_related('id_usuario').prefetch_related(
            'detalles__id_producto'
        )
        return Response(ProduccionSerializer(producciones, many=True).data)


class InventarioProductoTerminadoListView(APIView):
    """
    GET /api/productos-terminados/existencias/ — Existencias de pan terminado listo para la venta (CU12)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventarios = InventarioProductoTerminado.objects.select_related(
            'id_producto__id_categoria'
        ).order_by('id_producto__nombre')
        return Response(InventarioProductoTerminadoSerializer(inventarios, many=True).data)
