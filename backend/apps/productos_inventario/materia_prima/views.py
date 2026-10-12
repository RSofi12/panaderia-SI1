from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.productos_inventario.materia_prima.models import InventarioMateriaPrima, MateriaPrima
from apps.productos_inventario.materia_prima.permissions import PuedeGestionarMateriaPrima
from apps.productos_inventario.materia_prima.serializers import (
    MateriaPrimaSerializer,
    MateriaPrimaStockSerializer,
)


class MateriaPrimaListView(APIView):
    """GET/POST /api/materias-primas/ — Catálogo de insumos (CU7/CU8)."""
    permission_classes = [PuedeGestionarMateriaPrima]

    def get(self, request):
        materias = MateriaPrima.objects.select_related('inventario').prefetch_related('historial_precios')

        nombre = request.query_params.get('nombre')
        activo = request.query_params.get('activo')

        if nombre:
            materias = materias.filter(nombre__icontains=nombre.strip())
        if activo in ('true', 'false'):
            materias = materias.filter(activo=(activo == 'true'))

        materias = materias.order_by('nombre')
        return Response(MateriaPrimaSerializer(materias, many=True).data)

    def post(self, request):
        serializer = MateriaPrimaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            materia = serializer.save()
            InventarioMateriaPrima.objects.create(
                id_materia_prima=materia,
                stock_actual=0,
            )
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.ALTA_MATERIA_PRIMA,
                tabla_afectada='materia_prima',
                descripcion=f'Alta de materia prima {materia.nombre} ({materia.unidad_medida})',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(
            MateriaPrimaSerializer(materia).data,
            status=status.HTTP_201_CREATED,
        )


class MateriaPrimaDetailView(APIView):
    """PATCH /api/materias-primas/<id>/ — Edita datos del catálogo (CU8)."""
    permission_classes = [PuedeGestionarMateriaPrima]

    def patch(self, request, pk):
        materia = get_object_or_404(MateriaPrima, pk=pk)
        serializer = MateriaPrimaSerializer(materia, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            materia = serializer.save()
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.EDICION_MATERIA_PRIMA,
                tabla_afectada='materia_prima',
                descripcion=f'Edición de datos de la materia prima {materia.nombre}',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(MateriaPrimaSerializer(materia).data)


class MateriaPrimaToggleActivoView(APIView):
    """PATCH /api/materias-primas/<id>/toggle-activo/ — Baja lógica o reactivación."""
    permission_classes = [PuedeGestionarMateriaPrima]

    def patch(self, request, pk):
        materia = get_object_or_404(MateriaPrima, pk=pk)

        with transaction.atomic():
            materia.activo = not materia.activo
            materia.save(update_fields=['activo'])
            estado = 'activada' if materia.activo else 'inactivada'
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.CAMBIAR_ESTADO_MATERIA_PRIMA,
                tabla_afectada='materia_prima',
                descripcion=f'Materia prima {materia.nombre} {estado}',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(MateriaPrimaSerializer(materia).data)


class MateriaPrimaStockListView(APIView):
    """GET /api/inventario/materias-primas/ — Consulta de stock (CU8)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        materias = MateriaPrima.objects.select_related('inventario')

        nombre = request.query_params.get('nombre')
        activo = request.query_params.get('activo')
        bajo_minimo = request.query_params.get('bajo_minimo')

        if nombre:
            materias = materias.filter(nombre__icontains=nombre.strip())
        if activo in ('true', 'false'):
            materias = materias.filter(activo=(activo == 'true'))
        elif activo != 'all':
            materias = materias.filter(activo=True)
        if bajo_minimo == 'true':
            materias = materias.filter(inventario__stock_actual__lte=F('stock_minimo'))

        return Response(MateriaPrimaStockSerializer(materias, many=True).data)
