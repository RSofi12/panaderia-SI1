from django.db.models import Count, Q
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
    GET  /api/compras/ — Listado (sin líneas anidadas, con filtros)
    POST /api/compras/ — Registrar compra (CU7)
    """
    permission_classes = [PuedeRegistrarCompras]

    def get(self, request):
        queryset = (
            Compra.objects.select_related('id_proveedor', 'id_usuario')
            .annotate(cantidad_lineas=Count('detalles'))
            .order_by('-fecha_hora', '-id_compra')
        )

        id_proveedor = request.query_params.get('id_proveedor')
        if id_proveedor:
            queryset = queryset.filter(id_proveedor_id=id_proveedor)

        fecha_desde = request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_hora__date__gte=fecha_desde)

        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora__date__lte=fecha_hasta)

        search = request.query_params.get('search') or request.query_params.get('q')
        if search:
            search = search.strip()
            if search.isdigit():
                queryset = queryset.filter(
                    Q(id_compra=int(search)) | Q(id_proveedor__nombre__icontains=search)
                )
            else:
                queryset = queryset.filter(id_proveedor__nombre__icontains=search)

        return Response(CompraListSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = CompraRegistroSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        compra = serializer.save()
        advertencias = getattr(compra, 'advertencias', [])
        compra = Compra.objects.select_related(
            'id_proveedor',
            'id_usuario',
        ).prefetch_related('detalles__id_materia_prima').get(pk=compra.pk)
        compra.advertencias = advertencias
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
