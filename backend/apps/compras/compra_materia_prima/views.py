from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Compra
from .permissions import PuedeRegistrarCompras
from .serializers import (
    CompraListSerializer,
    CompraRegistroSerializer,
    CompraSerializer,
)


class CompraListCreateView(APIView):
    """
    GET  /api/compras/ — Listado (sin líneas anidadas)
    POST /api/compras/ — Registrar compra (CU7)
    """
    permission_classes = [PuedeRegistrarCompras]

    def get(self, request):
        compras = Compra.objects.select_related(
            'id_proveedor',
            'id_usuario',
        ).prefetch_related('detalles')
        return Response(CompraListSerializer(compras, many=True).data)

    def post(self, request):
        serializer = CompraRegistroSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        compra = serializer.save()
        compra = Compra.objects.select_related(
            'id_proveedor',
            'id_usuario',
        ).prefetch_related('detalles__id_materia_prima').get(pk=compra.pk)
        return Response(CompraSerializer(compra).data, status=status.HTTP_201_CREATED)


class CompraDetailView(APIView):
    """GET /api/compras/<id>/ — Detalle con líneas."""
    permission_classes = [PuedeRegistrarCompras]

    def get(self, request, pk):
        compra = get_object_or_404(
            Compra.objects.select_related('id_proveedor', 'id_usuario').prefetch_related(
                'detalles__id_materia_prima'
            ),
            pk=pk,
        )
        return Response(CompraSerializer(compra).data)
