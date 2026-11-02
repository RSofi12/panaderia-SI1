"""
Vistas para Producción Diaria (CU10) e Historial de Producción (CU11).
"""
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.productos_inventario.productos.models import Producto
from .consulta import leer_filtros_historial
from .exportar_produccion import csv_produccion, nombre_archivo, pdf_produccion, resumir_producciones
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
        filtros, error = leer_filtros_historial(request.query_params)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        producciones = get_historial_produccion(**filtros)
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


class ProduccionExportarView(APIView):
    """
    GET /api/produccion/csv/ y /api/produccion/pdf/

    Descarga las tarjetas y la tabla de Producción diaria. Usa los mismos
    filtros que el listado: fecha_desde, fecha_hasta y jornada.
    """

    permission_classes = [PuedeConsultarHistorialProduccion]
    formato = 'csv'

    def get(self, request):
        filtros, error = leer_filtros_historial(request.query_params)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        resumen = resumir_producciones(get_historial_produccion(**filtros), filtros)
        if self.formato == 'pdf':
            contenido = pdf_produccion(resumen)
            tipo = 'application/pdf'
            extension = 'pdf'
        else:
            contenido = csv_produccion(resumen)
            tipo = 'text/csv; charset=utf-8'
            extension = 'csv'

        respuesta = HttpResponse(contenido, content_type=tipo)
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo(filtros, extension)}"'
        return respuesta


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
