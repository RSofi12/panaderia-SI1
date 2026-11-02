from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reportes.permissions import PuedeGenerarReportes
from apps.reportes.serializers import (
    CierreReporteConsultaSerializer,
    CierreReporteVentasSerializer,
    ReporteVentasConsultaSerializer,
    ReporteVentasSerializer,
)
from apps.reportes.services.cierre_ventas import cierre_como_reporte, guardar_cierre, listar_cierres
from apps.reportes.services.exportar_reporte import csv_reporte, pdf_cierre
from apps.reportes.services.reporte_ventas import reporte_ventas


def _error_de_validacion(exc):
    if getattr(exc, 'message_dict', None):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(list(exc.messages)) from exc


class ReporteVentasView(APIView):
    """GET /api/reportes/ventas/?desde=&hasta= — CU21 dinámico. No guarda nada."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteVentasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_ventas(
                desde=datos['desde'],
                hasta=datos['hasta'],
                metodo_pago=datos.get('metodo_pago') or None,
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        return Response(ReporteVentasSerializer(reporte).data)


class ReporteVentasCsvView(APIView):
    """GET /api/reportes/ventas/csv/ — el mismo cálculo dinámico, en un archivo."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteVentasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        metodo = datos.get('metodo_pago') or None
        try:
            reporte = reporte_ventas(desde=datos['desde'], hasta=datos['hasta'], metodo_pago=metodo)
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        contenido = csv_reporte(reporte, metodo)
        respuesta = HttpResponse(contenido, content_type='text/csv; charset=utf-8')
        nombre = f'reporte-ventas-{reporte["desde"]}-{reporte["hasta"]}.csv'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


class CierresReporteVentasView(APIView):
    """GET lista los cierres. POST congela el cálculo de ese momento."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        cierres = [cierre_como_reporte(cierre) for cierre in listar_cierres()]
        return Response(CierreReporteVentasSerializer(cierres, many=True).data)

    def post(self, request):
        consulta = CierreReporteConsultaSerializer(data=request.data)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            cierre = guardar_cierre(
                usuario=request.user,
                desde=datos['desde'],
                hasta=datos['hasta'],
                periodo=datos['periodo'],
                metodo_pago=datos.get('metodo_pago') or None,
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        return Response(CierreReporteVentasSerializer(cierre).data, status=status.HTTP_201_CREATED)


class CierreReporteVentasDetailView(APIView):
    """GET /api/reportes/ventas/cierres/<id>/ — lee la copia, no vuelve a sumar."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request, id_cierre):
        cierre = get_object_or_404(listar_cierres(), pk=id_cierre)
        return Response(CierreReporteVentasSerializer(cierre_como_reporte(cierre)).data)


class CierreReporteVentasPdfView(APIView):
    """GET /api/reportes/ventas/cierres/<id>/pdf/ — PDF de la copia, no de una suma nueva."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request, id_cierre):
        cierre = get_object_or_404(listar_cierres(), pk=id_cierre)
        datos = cierre_como_reporte(cierre)
        respuesta = HttpResponse(pdf_cierre(datos), content_type='application/pdf')
        respuesta['Content-Disposition'] = f'attachment; filename="cierre-ventas-{cierre.id_cierre}.pdf"'
        return respuesta
