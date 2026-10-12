"""
Vistas para Producción Diaria (CU10) e Historial de Producción (CU11).
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Produccion
from .serializers import ProduccionSerializer


class ProduccionListCreateView(APIView):
    """
    GET  /api/produccion/ — Historial de producciones registradas (CU11)
    POST /api/produccion/ — Registrar producción diaria y descontar insumos (CU10 - Ciclo 2)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        producciones = Produccion.objects.select_related('id_usuario').prefetch_related(
            'detalles__id_producto'
        )
        return Response(ProduccionSerializer(producciones, many=True).data)
