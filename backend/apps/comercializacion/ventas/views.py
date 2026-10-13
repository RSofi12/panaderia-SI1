from datetime import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercializacion.ventas.models import Venta
from apps.comercializacion.ventas.permissions import PuedeRegistrarVentas
from apps.comercializacion.ventas.selectors import listar_ventas
from apps.comercializacion.ventas.serializers import (
    DetallesCotizacionSerializer,
    VentaListSerializer,
    VentaRegistroSerializer,
    VentaSerializer,
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
