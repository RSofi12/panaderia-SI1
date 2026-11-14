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

        queryset = gastos_filtrados(filtros)

        # Si el cliente solicita paginación (?page=), usamos el paginador de DRF
        if 'page' in request.query_params or 'page_size' in request.query_params:
            from rest_framework.pagination import PageNumberPagination
            paginator = PageNumberPagination()
            page_size = request.query_params.get('page_size')
            if page_size and page_size.isdigit():
                paginator.page_size = int(page_size)
            page = paginator.paginate_queryset(queryset, request)
            if page is not None:
                serializer = MovimientoEconomicoSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

        return Response(
            MovimientoEconomicoSerializer(queryset, many=True).data
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
    Acepta opcionalmente un campo 'motivo' en el cuerpo de la petición.
    """
    permission_classes = [PuedeGestionarGastos]

    def post(self, request, pk):
        get_object_or_404(MovimientoEconomico, pk=pk)
        motivo = request.data.get('motivo') if isinstance(request.data, dict) else None
        try:
            movimiento = anular_movimiento(
                usuario=request.user,
                id_movimiento=pk,
                motivo=motivo,
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
