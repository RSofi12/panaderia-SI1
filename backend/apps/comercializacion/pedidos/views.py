from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercializacion.pedidos.models import Pedido
from apps.comercializacion.pedidos.permissions import PuedeConsultarPedidos, PuedeRegistrarPedidos
from apps.comercializacion.pedidos.selectors import listar_pedidos, listar_pedidos_abiertos, obtener_pedido
from apps.comercializacion.pedidos.serializers import (
    CambiarEstadoPedidoSerializer,
    PedidoRegistroSerializer,
    PedidoSerializer,
)


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
