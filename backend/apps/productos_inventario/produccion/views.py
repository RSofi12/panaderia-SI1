"""
Vistas para Producción Diaria (CU10) e Historial de Producción (CU11).
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.productos_inventario.productos.models import Producto
from .models import Produccion
from .permissions import PuedeConsultarHistorialProduccion, PuedeRegistrarProduccion
from .selectors import get_historial_produccion
from .serializers import (
    ProduccionSerializer,
    RecetaProductoSerializer,
    RegistrarProduccionInputSerializer,
    SimularConsumoInputSerializer,
)
from .services import registrar_produccion_diaria, simular_consumo_produccion


class ProduccionListView(APIView):
    """
    GET /api/produccion/  — Historial de producciones registradas (CU11)
    POST /api/produccion/ — Registrar nueva producción diaria (CU10)
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [PuedeRegistrarProduccion()]
        return [PuedeConsultarHistorialProduccion()]

    def get(self, request):
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        jornada = request.query_params.get('jornada')
        id_producto = request.query_params.get('id_producto')

        if fecha_desde:
            try:
                date.fromisoformat(fecha_desde)
            except ValueError:
                return Response(
                    {'fecha_desde': 'Formato de fecha_desde inválido. Use AAAA-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if fecha_hasta:
            try:
                date.fromisoformat(fecha_hasta)
            except ValueError:
                return Response(
                    {'fecha_hasta': 'Formato de fecha_hasta inválido. Use AAAA-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return Response(
                {'fecha_desde': 'La fecha inicial no puede ser mayor que la fecha final.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if id_producto:
            try:
                int(id_producto)
            except (ValueError, TypeError):
                return Response(
                    {'id_producto': 'El identificador de producto debe ser un número entero válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        producciones = get_historial_produccion(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            jornada=jornada,
            id_producto=id_producto,
        )
        return Response(ProduccionSerializer(producciones, many=True).data)

    def post(self, request):
        serializer = RegistrarProduccionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        agente_usuario = request.META.get('HTTP_USER_AGENT')
        try:
            produccion = registrar_produccion_diaria(
                usuario=request.user,
                fecha=serializer.validated_data['fecha'],
                jornada=serializer.validated_data['jornada'],
                detalles_input=serializer.validated_data['detalles'],
                agente_usuario=agente_usuario,
            )
        except ValidationError as e:
            mensaje = e.message if hasattr(e, 'message') else (e.messages[0] if hasattr(e, 'messages') else str(e))
            return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)

        produccion_completa = (
            Produccion.objects
            .select_related('id_usuario')
            .prefetch_related(
                'detalles__id_producto',
                'movimientos_insumo__id_inventario__id_materia_prima'
            )
            .get(id_produccion=produccion.id_produccion)
        )
        return Response(ProduccionSerializer(produccion_completa).data, status=status.HTTP_201_CREATED)


class ProduccionDetailView(APIView):
    """Consulta detallada de una producción por su identificador (CU11)."""
    permission_classes = [PuedeConsultarHistorialProduccion]

    def get(self, request, id_produccion):
        produccion = get_object_or_404(
            Produccion.objects
            .select_related('id_usuario')
            .prefetch_related(
                'detalles__id_producto',
                'movimientos_insumo__id_inventario__id_materia_prima'
            ),
            id_produccion=id_produccion,
        )
        return Response(ProduccionSerializer(produccion).data)


class ProduccionSimularView(APIView):
    """
    POST /api/produccion/simular/ — Simulación y explosión de materiales en tiempo real (CU10).
    """
    permission_classes = [PuedeConsultarHistorialProduccion]

    def post(self, request):
        serializer = SimularConsumoInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        resultado = simular_consumo_produccion(serializer.validated_data['detalles'])
        return Response(resultado, status=status.HTTP_200_OK)


class RecetasListView(APIView):
    """
    GET /api/produccion/recetas/ — Catálogo de recetas (BOM) por producto activo.
    """
    permission_classes = [PuedeConsultarHistorialProduccion]

    def get(self, request):
        productos = (
            Producto.objects
            .filter(activo=True)
            .prefetch_related('receta_detalles__id_materia_prima')
            .order_by('id_producto')
        )
        return Response(RecetaProductoSerializer(productos, many=True).data)
