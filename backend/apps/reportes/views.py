from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reportes.permissions import PuedeGenerarReportes
from apps.reportes.serializers import (
    ReporteVentasConsultaSerializer,
    ReporteVentasSerializer,
)
from apps.reportes.services.exportar_reporte import csv_reporte, pdf_reporte_ventas
from apps.reportes.services.reporte_ventas import reporte_ventas


def _error_de_validacion(exc):
    if getattr(exc, 'message_dict', None):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(list(exc.messages)) from exc


def _parsear_columnas(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    cols = [c.strip().lower() for c in raw.split(',') if c.strip()]
    return cols or None


class ReporteVentasView(APIView):
    """GET /api/reportes/ventas/?desde=&hasta=&metodo_pago= — CU21 dinámico."""

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
    """GET /api/reportes/ventas/csv/ — Exportación a archivo CSV del reporte dinámico."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteVentasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        metodo = datos.get('metodo_pago') or None
        columnas = _parsear_columnas(request.query_params.get('columnas'))
        try:
            reporte = reporte_ventas(desde=datos['desde'], hasta=datos['hasta'], metodo_pago=metodo)
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        contenido = csv_reporte(reporte, metodo, columnas)
        respuesta = HttpResponse(contenido, content_type='text/csv; charset=utf-8-sig')
        nombre = f'reporte-ventas-{reporte["desde"]}-{reporte["hasta"]}.csv'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


class ReporteVentasPdfView(APIView):
    """GET /api/reportes/ventas/pdf/ — Exportación a PDF con soporte de selección dinámica de columnas."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteVentasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        metodo = datos.get('metodo_pago') or None
        columnas = _parsear_columnas(request.query_params.get('columnas'))
        try:
            reporte = reporte_ventas(desde=datos['desde'], hasta=datos['hasta'], metodo_pago=metodo)
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        contenido = pdf_reporte_ventas(reporte, metodo, columnas)
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        nombre = f'reporte-ventas-{reporte["desde"]}-{reporte["hasta"]}.pdf'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta
