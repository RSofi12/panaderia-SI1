from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reportes.permissions import PuedeGenerarReportes
from apps.reportes.serializers import (
    InterpretarComandoVozEntradaSerializer,
    InterpretarComandoVozSalidaSerializer,
    ReporteResultadosEconomicosConsultaSerializer,
    ReporteResultadosEconomicosSerializer,
    ReporteVentasConsultaSerializer,
    ReporteVentasSerializer,
)
from apps.reportes.services.exportar_reporte import csv_reporte, pdf_reporte_ventas
from apps.reportes.services.exportar_resultados_economicos import (
    csv_resultados_economicos,
    pdf_resultados_economicos,
)
from apps.reportes.services.interprete_voz import interpretar_comando_voz
from apps.reportes.services.reporte_resultados_economicos import reporte_resultados_economicos
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


def _rechazar_exportacion_sin_datos(reporte: dict) -> None:
    if reporte.get('cantidad', 0) == 0:
        raise serializers.ValidationError(
            {'detail': 'No hay datos disponibles para el período solicitado.'}
        )


class ReporteInterpretarVozView(APIView):
    """POST /api/reportes/voz/interpretar/ — CU21–CU25 (voz/texto + Gemini o fallback local)."""

    permission_classes = [PuedeGenerarReportes]

    def post(self, request):
        entrada = InterpretarComandoVozEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        cu_actual = (datos.get('cu_actual') or '').strip() or None
        try:
            resultado = interpretar_comando_voz(datos['texto'], cu_actual=cu_actual)
        except ValueError as exc:
            raise serializers.ValidationError({'texto': str(exc)}) from exc
        salida = InterpretarComandoVozSalidaSerializer(resultado)
        return Response(salida.data, status=status.HTTP_200_OK)


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
        _rechazar_exportacion_sin_datos(reporte)
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
        _rechazar_exportacion_sin_datos(reporte)
        contenido = pdf_reporte_ventas(reporte, metodo, columnas)
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        nombre = f'reporte-ventas-{reporte["desde"]}-{reporte["hasta"]}.pdf'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


# =============================================================================
# VISTAS PARA CU25: RESULTADOS ECONÓMICOS
# =============================================================================

class ReporteResultadosEconomicosView(APIView):
    """GET /api/reportes/resultados-economicos/?desde=&hasta= — CU25."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteResultadosEconomicosConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_resultados_economicos(
                desde=datos['desde'],
                hasta=datos['hasta'],
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        return Response(ReporteResultadosEconomicosSerializer(reporte).data)


class ReporteResultadosEconomicosCsvView(APIView):
    """GET /api/reportes/resultados-economicos/csv/ — Exportación CSV (Excel) de resultados económicos."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteResultadosEconomicosConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_resultados_economicos(desde=datos['desde'], hasta=datos['hasta'])
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        if not reporte.get('tiene_movimientos'):
            raise serializers.ValidationError(
                {'detail': 'No hay movimientos económicos registrados para el período solicitado.'}
            )
        contenido = csv_resultados_economicos(reporte)
        respuesta = HttpResponse(contenido, content_type='text/csv; charset=utf-8-sig')
        nombre = f'resultados-economicos-{reporte["desde"]}-{reporte["hasta"]}.csv'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


class ReporteResultadosEconomicosPdfView(APIView):
    """GET /api/reportes/resultados-economicos/pdf/ — Exportación PDF formal de resultados económicos."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteResultadosEconomicosConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_resultados_economicos(desde=datos['desde'], hasta=datos['hasta'])
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        if not reporte.get('tiene_movimientos'):
            raise serializers.ValidationError(
                {'detail': 'No hay movimientos económicos registrados para el período solicitado.'}
            )
        contenido = pdf_resultados_economicos(reporte)
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        nombre = f'resultados-economicos-{reporte["desde"]}-{reporte["hasta"]}.pdf'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta

