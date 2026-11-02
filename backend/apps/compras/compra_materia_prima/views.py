from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .consulta import compras_filtradas, leer_filtros_compra
from .exportar_compra import csv_compras, nombre_archivo, pdf_compras, resumir_compras
from .models import Compra
from .permissions import PuedeRegistrarCompras
from .serializers import (
    CompraListSerializer,
    CompraRegistroSerializer,
    CompraSerializer,
)


class CompraListCreateView(APIView):
    """
    GET  /api/compras/ — Listado (sin líneas anidadas, con filtros)
    POST /api/compras/ — Registrar compra (CU7)
    """
    permission_classes = [PuedeRegistrarCompras]

    def get(self, request):
        filtros, error = leer_filtros_compra(request.query_params)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        return Response(CompraListSerializer(compras_filtradas(filtros), many=True).data)

    def post(self, request):
        serializer = CompraRegistroSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        compra = serializer.save()
        advertencias = getattr(compra, 'advertencias', [])
        compra = Compra.objects.select_related(
            'id_proveedor',
            'id_usuario',
        ).prefetch_related('detalles__id_materia_prima').get(pk=compra.pk)
        compra.advertencias = advertencias
        return Response(CompraSerializer(compra).data, status=status.HTTP_201_CREATED)


class CompraExportarView(APIView):
    """
    GET /api/compras/csv/ y /api/compras/pdf/

    Descarga las tarjetas y la tabla de Compras. Usa los mismos filtros
    que el listado: proveedor, rango de fechas y texto de búsqueda.
    """

    permission_classes = [PuedeRegistrarCompras]
    formato = 'csv'

    def get(self, request):
        filtros, error = leer_filtros_compra(request.query_params)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        resumen = resumir_compras(filtros)
        if self.formato == 'pdf':
            contenido = pdf_compras(resumen)
            tipo = 'application/pdf'
            extension = 'pdf'
        else:
            contenido = csv_compras(resumen)
            tipo = 'text/csv; charset=utf-8'
            extension = 'csv'

        respuesta = HttpResponse(contenido, content_type=tipo)
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo(filtros, extension)}"'
        return respuesta


class CompraDetailView(APIView):
    """GET /api/compras/<id>/ — Detalle con líneas."""
    permission_classes = [PuedeRegistrarCompras]

    def get(self, request, pk):
        compra = get_object_or_404(
            Compra.objects.select_related('id_proveedor', 'id_usuario').prefetch_related(
                'detalles__id_materia_prima'
            ),
            pk=pk,
        )
        return Response(CompraSerializer(compra).data)
