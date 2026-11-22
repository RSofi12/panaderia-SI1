from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercializacion.pedidos.models import EstadoPedido, Pedido
from apps.comercializacion.pedidos.permissions import PuedeConsultarPedidos, PuedeRegistrarPedidos
from apps.comercializacion.pedidos.selectors import listar_pedidos, listar_pedidos_abiertos, obtener_pedido
from apps.comercializacion.pedidos.serializers import (
    CambiarEstadoPedidoSerializer,
    PagarPedidoSerializer,
    PedidoCobroSerializer,
    PedidoRegistroSerializer,
    PedidoSerializer,
)
from apps.comercializacion.ventas.models import MetodoPago
from apps.comercializacion.ventas.services.stripe_pago import crear_intencion


def _error_de_validacion(exc: DjangoValidationError):
    if getattr(exc, 'message_dict', None):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(list(exc.messages)) from exc


class PedidoCreateView(APIView):
    """POST /api/pedidos/ — alta en estado pendiente. GET lista los que siguen abiertos."""
    permission_classes = [PuedeRegistrarPedidos]

    def get(self, request):
        return Response(PedidoSerializer(listar_pedidos_abiertos(), many=True).data)

    def post(self, request):
        serializer = PedidoRegistroSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        pedido = (
            Pedido.objects.select_related('id_cliente', 'id_usuario')
            .prefetch_related('detalles__id_producto')
            .get(pk=pedido.pk)
        )
        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)


class PedidoDetailView(APIView):
    """GET lee el pedido. PATCH cambia el estado, sin entregarlo."""
    permission_classes = [PuedeRegistrarPedidos]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [PuedeConsultarPedidos()]
        return [PuedeRegistrarPedidos()]

    def get(self, request, pk):
        return Response(PedidoSerializer(obtener_pedido(pk)).data)

    def patch(self, request, pk):
        pedido = obtener_pedido(pk)
        serializer = CambiarEstadoPedidoSerializer(
            instance=pedido,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response(PedidoSerializer(obtener_pedido(pedido.pk)).data)


class PedidoEstadoListView(APIView):
    """GET /api/pedidos/estado/ — CU15, consulta filtrable de todos los pedidos."""

    permission_classes = [PuedeConsultarPedidos]

    def get(self, request):
        estado = request.query_params.get('estado', '').strip().lower()
        q = request.query_params.get('q', '').strip()
        fecha_entrega = request.query_params.get('fecha_entrega', '').strip()
        return Response(PedidoSerializer(listar_pedidos(estado, q, fecha_entrega), many=True).data)


class PedidoEstadoDetailView(APIView):
    """GET /api/pedidos/estado/<id>/ — CU15, detalle de un pedido."""

    permission_classes = [PuedeConsultarPedidos]

    def get(self, request, pk):
        return Response(PedidoSerializer(obtener_pedido(pk)).data)


class PedidoPagoView(APIView):
    """POST /api/pedidos/<id>/pago/ — cobra el pedido y lo deja en el mismo estado."""
    permission_classes = [PuedeRegistrarPedidos]

    def post(self, request, pk):
        pedido = obtener_pedido(pk)
        serializer = PagarPedidoSerializer(
            instance=pedido,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response(PedidoSerializer(obtener_pedido(pedido.pk)).data)


class PedidoStripeConfigView(APIView):
    """GET /api/pedidos/stripe/config/ — clave pública para el formulario de tarjeta."""
    permission_classes = [PuedeRegistrarPedidos]

    def get(self, request):
        clave = (getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '') or '').strip().strip("'\"")
        return Response({'publishable_key': clave})


class PedidoStripeCarritoView(APIView):
    """POST /api/pedidos/stripe/intencion/ — pasarela del carrito, antes de guardar."""
    permission_classes = [PuedeRegistrarPedidos]

    def post(self, request):
        serializer = PedidoCobroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_201_CREATED)


class PedidoStripeIntencionView(APIView):
    """
    POST /api/pedidos/<id>/stripe/intencion/
    Prepara el cobro del total congelado. No entrega el pedido ni toca el stock.
    """
    permission_classes = [PuedeRegistrarPedidos]

    def post(self, request, pk):
        pedido = obtener_pedido(pk)
        if (
            pedido.pagado
            or pedido.metodo_pago != MetodoPago.STRIPE
            or pedido.estado in (EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO)
        ):
            raise serializers.ValidationError({
                'pago': 'La tarjeta se ingresa para pagar un pedido que todavía no está cobrado.',
            })
        try:
            return Response(
                crear_intencion(monto=pedido.total, origen='cu14-pedido'),
                status=status.HTTP_201_CREATED,
            )
        except DjangoValidationError as exc:
            _error_de_validacion(exc)
