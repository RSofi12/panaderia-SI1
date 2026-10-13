"""
Vistas para Producción Diaria (CU10) e Historial de Producción (CU11).
"""
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Produccion
from .permissions import PuedeConsultarHistorialProduccion
from .selectors import get_historial_produccion
from .serializers import ProduccionSerializer


class ProduccionListView(APIView):
    """
    GET /api/produccion/ — Historial de producciones registradas (CU11)
    """
    permission_classes = [PuedeConsultarHistorialProduccion]

    def get(self, request):
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        jornada = request.query_params.get('jornada')
        id_producto = request.query_params.get('id_producto')

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return Response(
                {'detail': 'La fecha inicial no puede ser mayor que la fecha final.'},
                status=400,
            )

        producciones = get_historial_produccion(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            jornada=jornada,
            id_producto=id_producto,
        )
        return Response(ProduccionSerializer(producciones, many=True).data)


class ProduccionDetailView(APIView):
    """Consulta detallada de una producción por su identificador."""
    permission_classes = [PuedeConsultarHistorialProduccion]

    def get(self, request, id_produccion):
        produccion = get_object_or_404(
            Produccion.objects.select_related('id_usuario').prefetch_related('detalles__id_producto'),
            id_produccion=id_produccion,
        )
        return Response(ProduccionSerializer(produccion).data)
