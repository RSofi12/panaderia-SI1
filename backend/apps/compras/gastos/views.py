from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .consulta import gastos_filtrados, leer_filtros_gasto
from .models import MovimientoEconomico
from .permissions import PuedeGestionarGastos
from .serializers import (
    MovimientoEconomicoRegistroSerializer,
    MovimientoEconomicoSerializer,
)
from .services.registrar_movimiento import anular_movimiento


class GastoListCreateView(APIView):
    """
    GET  /api/gastos/ — Listado con filtros ?tipo=, ?categoria=, ?fecha_desde=,
                        ?fecha_hasta=, ?anulado= y ?search=
    POST /api/gastos/ — Registrar gasto o inversión (CU20)
    """
    permission_classes = [PuedeGestionarGastos]

    def get(self, request):
        filtros, error = leer_filtros_gasto(request.query_params)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            MovimientoEconomicoSerializer(gastos_filtrados(filtros), many=True).data
        )

    def post(self, request):
        serializer = MovimientoEconomicoRegistroSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        movimiento = serializer.save()
        movimiento = MovimientoEconomico.objects.select_related('id_usuario').get(
            pk=movimiento.pk
        )
        return Response(
            MovimientoEconomicoSerializer(movimiento).data,
            status=status.HTTP_201_CREATED,
        )


class GastoDetailView(APIView):
    """GET /api/gastos/<id>/ — Detalle de un movimiento económico."""
    permission_classes = [PuedeGestionarGastos]

    def get(self, request, pk):
        movimiento = get_object_or_404(
            MovimientoEconomico.objects.select_related('id_usuario'),
            pk=pk,
        )
        return Response(MovimientoEconomicoSerializer(movimiento).data)


class GastoAnularView(APIView):
    """
    POST /api/gastos/<id>/anular/ — Anula el movimiento sin borrarlo (CU20).

    Un egreso real no se elimina: se marca `anulado` y queda la traza en
    bitácora. El listado lo excluye por defecto.
    """
    permission_classes = [PuedeGestionarGastos]

    def post(self, request, pk):
        get_object_or_404(MovimientoEconomico, pk=pk)
        try:
            movimiento = anular_movimiento(
                usuario=request.user,
                id_movimiento=pk,
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {'detail': list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(MovimientoEconomicoSerializer(movimiento).data)
