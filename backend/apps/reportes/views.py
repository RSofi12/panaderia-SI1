from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reportes.permissions import PuedeGenerarReportes
from apps.reportes.serializers import (
    CierreReporteComprasConsultaSerializer,
    CierreReporteComprasSerializer,
    InterpretarComandoVozEntradaSerializer,
    InterpretarComandoVozSalidaSerializer,
    ReporteComprasConsultaSerializer,
    ReporteComprasSerializer,
    ReporteExistenciasConsultaSerializer,
    ReporteExistenciasSerializer,
    ReporteVentasConsultaSerializer,
    ReporteVentasSerializer,
)
from apps.reportes.services.cierre_compras import (
    cierre_como_reporte as cierre_compras_como_reporte,
    guardar_cierre_compras,
    listar_cierres_compras,
)
from apps.reportes.services.exportar_reporte import csv_reporte, pdf_reporte_ventas
from apps.reportes.services.exportar_reporte_compras import csv_reporte_compras, pdf_cierre_compras
from apps.reportes.services.interprete_voz import interpretar_comando_voz
from apps.reportes.services.reporte_compras import reporte_compras
from apps.reportes.services.reporte_existencias import reporte_existencias
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


# ==============================================================================
# CU21: Reporte de ventas
# ==============================================================================

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


# ==============================================================================
# CU23: Reporte de existencias
# ==============================================================================

class ReporteExistenciasView(APIView):
    """GET /api/reportes/existencias/ — CU23, sin modificar inventarios."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteExistenciasConsultaSerializer(data=request.query_params.dict())
        consulta.is_valid(raise_exception=True)
        reporte = reporte_existencias(**consulta.validated_data)
        return Response(ReporteExistenciasSerializer(reporte).data)


# ==============================================================================
# CU24: Generar reporte de compras y gastos
# ==============================================================================

class ReporteComprasView(APIView):
    """GET /api/reportes/compras/?desde=&hasta=&id_proveedor=&id_materia_prima= — CU24 dinámico."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteComprasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_compras(
                desde=datos['desde'],
                hasta=datos['hasta'],
                id_proveedor=datos.get('id_proveedor'),
                id_materia_prima=datos.get('id_materia_prima'),
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        return Response(ReporteComprasSerializer(reporte).data)


class ReporteComprasCsvView(APIView):
    """GET /api/reportes/compras/csv/ — cálculo dinámico en CSV delimitado por ';'."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        consulta = ReporteComprasConsultaSerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            reporte = reporte_compras(
                desde=datos['desde'],
                hasta=datos['hasta'],
                id_proveedor=datos.get('id_proveedor'),
                id_materia_prima=datos.get('id_materia_prima'),
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)

        nombre_prov = None
        if datos.get('id_proveedor') and reporte['proveedores']:
            nombre_prov = reporte['proveedores'][0]['nombre']

        contenido = csv_reporte_compras(reporte, nombre_prov)
        respuesta = HttpResponse(contenido, content_type='text/csv; charset=utf-8')
        nombre = f'reporte-compras-{reporte["desde"]}-{reporte["hasta"]}.csv'
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
        return respuesta


class CierresReporteComprasView(APIView):
    """GET lista los cierres de compras. POST congela el cálculo de ese momento."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request):
        cierres = [cierre_compras_como_reporte(cierre) for cierre in listar_cierres_compras()]
        return Response(CierreReporteComprasSerializer(cierres, many=True).data)

    def post(self, request):
        consulta = CierreReporteComprasConsultaSerializer(data=request.data)
        consulta.is_valid(raise_exception=True)
        datos = consulta.validated_data
        try:
            cierre = guardar_cierre_compras(
                usuario=request.user,
                desde=datos['desde'],
                hasta=datos['hasta'],
                periodo=datos['periodo'],
                id_proveedor=datos.get('id_proveedor'),
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
        return Response(CierreReporteComprasSerializer(cierre).data, status=status.HTTP_201_CREATED)


class CierreReporteComprasDetailView(APIView):
    """GET /api/reportes/compras/cierres/<id>/ — lee la copia congelada en BD."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request, id_cierre):
        cierre = get_object_or_404(listar_cierres_compras(), pk=id_cierre)
        return Response(CierreReporteComprasSerializer(cierre_compras_como_reporte(cierre)).data)


class CierreReporteComprasPdfView(APIView):
    """GET /api/reportes/compras/cierres/<id>/pdf/ — PDF del cierre congelado."""

    permission_classes = [PuedeGenerarReportes]

    def get(self, request, id_cierre):
        cierre = get_object_or_404(listar_cierres_compras(), pk=id_cierre)
        datos = cierre_compras_como_reporte(cierre)
        respuesta = HttpResponse(pdf_cierre_compras(datos), content_type='application/pdf')
        respuesta['Content-Disposition'] = f'attachment; filename="cierre-compras-{cierre.id_cierre}.pdf"'
        return respuesta
