from django.http import HttpResponse
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercializacion.ventas.models import Venta
from apps.comercializacion.ventas.permissions import PuedeConsultarComprobante, PuedeRegistrarVentas
from apps.comercializacion.ventas.selectors import listar_ventas, obtener_comprobante_venta
from apps.comercializacion.ventas.serializers import (
    DetallesCotizacionSerializer,
    VentaListSerializer,
    VentaRegistroSerializer,
    VentaSerializer,
    ComprobanteVentaSerializer,
)
from apps.comercializacion.ventas.services.registrar_venta import (
    asegurar_stock_disponible,
    cotizar_detalles,
)
from apps.comercializacion.ventas.services.stripe_pago import crear_intencion


def _error_de_validacion(exc: DjangoValidationError):
    if getattr(exc, 'message_dict', None):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(list(exc.messages)) from exc


class VentaListCreateView(APIView):
    """
    GET  /api/ventas/?fecha=YYYY-MM-DD
    POST /api/ventas/
    """
    permission_classes = [PuedeRegistrarVentas]

    def get(self, request):
        fecha_texto = request.query_params.get('fecha')
        fecha = None
        if fecha_texto:
            try:
                fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'fecha': ['Usa el formato YYYY-MM-DD.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(VentaListSerializer(listar_ventas(fecha=fecha), many=True).data)

    def post(self, request):
        serializer = VentaRegistroSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        venta = serializer.save()
        stock = getattr(venta, 'stock_resultante', [])
        venta = (
            Venta.objects.select_related('id_usuario')
            .prefetch_related('detalles__id_producto')
            .get(pk=venta.pk)
        )
        venta.stock_resultante = stock
        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)


class VentaDetailView(APIView):
    permission_classes = [PuedeRegistrarVentas]

    def get(self, request, pk):
        venta = get_object_or_404(
            Venta.objects.select_related('id_usuario').prefetch_related('detalles__id_producto'),
            pk=pk,
        )
        return Response(VentaSerializer(venta).data)


class IntencionStripeView(APIView):
    """
    POST /api/ventas/stripe/intencion/
    Crea el PaymentIntent. No escribe la venta ni descuenta stock.
    """
    permission_classes = [PuedeRegistrarVentas]

    def post(self, request):
        serializer = DetallesCotizacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            lineas, total = cotizar_detalles(serializer.validated_data['detalles'])
            asegurar_stock_disponible(lineas)
            return Response(crear_intencion(monto=total), status=status.HTTP_201_CREATED)
        except DjangoValidationError as exc:
            _error_de_validacion(exc)


class StripeConfigView(APIView):
    """
    GET /api/ventas/stripe/config/
    Retorna la clave pública de Stripe (pk_test_...) configurada en el servidor.
    """
    permission_classes = [PuedeRegistrarVentas]

    def get(self, request):
        pk = (
            getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
            or getattr(settings, 'VITE_STRIPE_PUBLISHABLE_KEY', '')
            or ''
        ).strip().strip("'\"")
        return Response({'publishable_key': pk})


class VentaComprobanteView(APIView):
    """
    GET /api/ventas/<pk>/comprobante/
    Retorna la estructura de datos completa del comprobante de venta (CU16).
    Audita la consulta en la bitácora del sistema (CU26).
    """
    permission_classes = [PuedeConsultarComprobante]

    def get(self, request, pk):
        venta = obtener_comprobante_venta(pk)
        if not venta:
            return Response(
                {'detail': 'No se encontró la venta o comprobante especificado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = ComprobanteVentaSerializer(venta).data

        # Auditoría CU26
        try:
            from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
            Bitacora.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                accion=AccionBitacora.EMISION_COMPROBANTE,
                tabla_afectada='venta',
                agente_usuario=(request.META.get('HTTP_USER_AGENT') or '')[:255],
            )
        except Exception:
            pass

        return Response(data, status=status.HTTP_200_OK)


class VentaComprobantePdfView(APIView):
    """
    GET /api/ventas/<pk>/comprobante/pdf/
    Genera y transmite el comprobante en formato binario PDF para impresión o descarga.
    """
    permission_classes = [PuedeConsultarComprobante]

    def get(self, request, pk):
        venta = obtener_comprobante_venta(pk)
        if not venta:
            return Response(
                {'detail': 'No se encontró la venta o comprobante especificado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.comercializacion.ventas.services.comprobante_pdf import generar_ticket_pdf_bytes

        data = ComprobanteVentaSerializer(venta).data
        pdf_bytes = generar_ticket_pdf_bytes(data)

        # Auditoría CU26
        try:
            from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
            Bitacora.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                accion=AccionBitacora.EMISION_COMPROBANTE,
                tabla_afectada='venta',
                agente_usuario=(request.META.get('HTTP_USER_AGENT') or '')[:255],
            )
        except Exception:
            pass

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'comprobante_{venta.numero_comprobante}.pdf'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

